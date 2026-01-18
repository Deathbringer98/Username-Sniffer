# advanced_username_recon.py
from __future__ import annotations

import aiohttp
import asyncio
import json
import argparse
import csv
import re
import random
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()


# ----------------------------
# Username variations
# ----------------------------
def generate_username_variations(base: str, max_variants: int = 15) -> List[str]:
    base = base.strip().lower()
    variations = {base}

    number_suffixes = [str(random.randint(0, 99)), "123", "69", "88", "tv", "yt", "x", "official"]
    year_suffixes = [str(y) for y in range(1990, 2027)]
    simple_suffixes = ["_", "__", ".", "pro", "real", "hq", "fan", "live"]

    for suffix in (number_suffixes + year_suffixes + simple_suffixes):
        if len(variations) >= max_variants:
            break
        variations.add(base + suffix)
        variations.add(base + "_" + suffix)
        variations.add(base + "." + suffix)

    if len(base) > 4:
        mid = len(base) // 2
        variations.add(base[:mid] + "_" + base[mid:])
        variations.add(base[:mid] + "." + base[mid:])

    prefixes = ["the", "real", "mr", "ms", "official"]
    for prefix in prefixes:
        variations.add(prefix + base)
        variations.add(prefix + "_" + base)

    var_list = list(variations)
    random.shuffle(var_list)
    return var_list[:max_variants]


# ----------------------------
# Sites loading + regex compile
# ----------------------------
def load_sites(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"sites.json not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        sites = json.load(f)

    if not isinstance(sites, dict):
        raise ValueError("sites.json must be a JSON object mapping site_name -> config")

    for _, cfg in sites.items():
        nfr = cfg.get("not_found_regex")
        cfg["_not_found_re"] = re.compile(nfr, re.IGNORECASE) if nfr else None

        brr = cfg.get("bad_redirect_regex")
        cfg["_bad_redirect_re"] = re.compile(brr, re.IGNORECASE) if brr else None

        # Optional: treat these as "exists" only if this regex is present in HTML
        must = cfg.get("must_contain_regex")
        cfg["_must_re"] = re.compile(must, re.IGNORECASE) if must else None

    return sites


def is_x_site(site_name: str, site_data: Dict[str, Any]) -> bool:
    s = site_name.strip().lower()
    if s in {"twitter", "twitter/x", "x"}:
        return True
    url = str(site_data.get("url", "")).lower()
    return ("x.com/{}" in url) or ("twitter.com/{}" in url)


# ----------------------------
# Networking helpers
# ----------------------------
async def read_limited_text(resp: aiohttp.ClientResponse, limit_chars: int = 120_000) -> str:
    chunks: List[str] = []
    read = 0
    async for chunk in resp.content.iter_chunked(8192):
        s = chunk.decode(errors="ignore")
        chunks.append(s)
        read += len(s)
        if read >= limit_chars:
            break
    return "".join(chunks)


def looks_like_bad_redirect(site_data: Dict[str, Any], resp: aiohttp.ClientResponse) -> bool:
    """
    If we got redirected to login/join/etc, it's not a clean "exists".
    """
    bad_re = site_data.get("_bad_redirect_re")
    if not bad_re:
        return False

    # Check final URL + redirect chain URLs
    final_url = str(resp.url)
    if bad_re.search(final_url):
        return True

    for h in resp.history:
        if bad_re.search(str(h.url)):
            return True

    return False


async def interpret_response(
    site_name: str,
    site_data: Dict[str, Any],
    url: str,
    resp: aiohttp.ClientResponse,
) -> Tuple[str, Optional[bool], str]:
    status = resp.status

    # hard not found
    if status in (404, 410):
        return site_name, False, url

    # if we got redirected into a "bad" area (login/join), treat as uncertain
    if looks_like_bad_redirect(site_data, resp):
        return site_name, None, url

    # Most sites: 200 alone is not proof.
    if status == 200:
        not_found_re = site_data.get("_not_found_re")
        must_re = site_data.get("_must_re")

        # If we have regex rules, apply them
        if not_found_re or must_re:
            text = await read_limited_text(resp, limit_chars=120_000)

            if not_found_re and not_found_re.search(text):
                return site_name, False, url

            if must_re:
                # Only "exists" if "must contain" is present; otherwise uncertain
                if must_re.search(text):
                    return site_name, True, url
                return site_name, None, url

            # If not_found_regex exists and didn't match => likely exists
            return site_name, True, url

        # No regex rules configured => 200 is too weak; mark uncertain
        return site_name, None, url

    # Common blocked/throttled/weird statuses
    if status in (301, 302, 303, 307, 308, 401, 403, 405, 429, 500, 502, 503):
        return site_name, None, url

    return site_name, None, url


async def check_username(
    session: aiohttp.ClientSession,
    sem: asyncio.Semaphore,
    site_name: str,
    site_data: Dict[str, Any],
    username: str,
    proxy: Optional[str],
    timeout_total: float,
) -> Tuple[str, Optional[bool], str]:
    url = str(site_data["url"]).format(username)
    method = str(site_data.get("method", "HEAD")).upper()

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    timeout = aiohttp.ClientTimeout(total=timeout_total)

    def request(m: str):
        return session.request(
            m,
            url,
            headers=headers,
            proxy=proxy,
            timeout=timeout,
            allow_redirects=True,
        )

    for attempt in range(3):
        try:
            async with sem:
                async with request(method) as resp:
                    # if HEAD is blocked, try GET
                    if method == "HEAD" and resp.status in (403, 405, 429, 500, 502, 503):
                        async with request("GET") as resp2:
                            return await interpret_response(site_name, site_data, url, resp2)
                    return await interpret_response(site_name, site_data, url, resp)

        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt == 2:
                return site_name, None, url
            await asyncio.sleep(0.25 * (2 ** attempt))
        except Exception:
            if attempt == 2:
                return site_name, None, url
            await asyncio.sleep(0.25 * (2 ** attempt))

    return site_name, None, url


async def fetch_x_bio(
    session: aiohttp.ClientSession,
    username: str,
    proxy: Optional[str],
    timeout_total: float,
) -> Optional[str]:
    url = f"https://x.com/{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    timeout = aiohttp.ClientTimeout(total=timeout_total)

    try:
        async with session.get(url, proxy=proxy, timeout=timeout, headers=headers, allow_redirects=True) as resp:
            if resp.status != 200:
                return None
            text = await resp.text(errors="ignore")

            match = re.search(r'data-testid="UserDescription"[^>]*>(.*?)</div>', text, re.DOTALL | re.IGNORECASE)
            if match:
                bio = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                bio = re.sub(r"\s+", " ", bio)
                return (bio[:80] + "...") if len(bio) > 80 else bio

            meta_match = re.search(r'<meta\s+name="description"\s+content="(.*?)"', text, re.IGNORECASE)
            if meta_match:
                bio = re.sub(r"\s+", " ", meta_match.group(1).strip())
                return (bio[:80] + "...") if len(bio) > 80 else bio

            return None
    except Exception:
        return None


# ----------------------------
# UI
# ----------------------------
def build_hits_table(username: str, results: List[Tuple[str, Optional[bool], str]]) -> Table:
    hits = [(site, url) for site, exists, url in results if exists is True]

    table = Table(
        title=f"Found accounts for @{username}",
        title_style="bold green",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        expand=True,
    )
    table.add_column("Site", style="bold", width=22)
    table.add_column("URL", style="dim blue", overflow="fold")

    for site, url in sorted(hits, key=lambda x: x[0].lower()):
        table.add_row(site, url)

    table.caption = f"[bold]{len(hits)}[/bold] sites matched"
    table.caption_style = "italic green"
    return table


def build_uncertain_table(username: str, results: List[Tuple[str, Optional[bool], str]]) -> Table:
    uncertain = [(site, url) for site, exists, url in results if exists is None]

    table = Table(
        title=f"Uncertain (blocked/redirect/login) for @{username}",
        title_style="bold yellow",
        show_header=True,
        header_style="bold magenta",
        box=box.ROUNDED,
        expand=True,
    )
    table.add_column("Site", style="bold", width=22)
    table.add_column("URL", style="dim blue", overflow="fold")

    for site, url in sorted(uncertain, key=lambda x: x[0].lower()):
        table.add_row(site, url)

    table.caption = f"[bold]{len(uncertain)}[/bold] uncertain"
    table.caption_style = "italic yellow"
    return table


def print_summary(summary_data: List[Tuple[str, int, int]]) -> None:
    summary_table = Table(title="Summary", title_style="bold green", box=box.MINIMAL)
    summary_table.add_column("Username", style="cyan")
    summary_table.add_column("Hits", justify="right")
    summary_table.add_column("Sites")

    for uname, hits, total_sites in sorted(summary_data, key=lambda x: x[1], reverse=True):
        color = "green" if hits > 5 else "yellow" if hits >= 1 else "red"
        summary_table.add_row(uname, f"[{color} bold]{hits}[/{color} bold]", str(total_sites))

    console.print(summary_table)


# ----------------------------
# Main scanning
# ----------------------------
async def run_scan(args, username: str):
    sites_all = load_sites(Path(args.sites))

    # Skip unreliable entries unless user explicitly includes them
    sites: Dict[str, Dict[str, Any]] = {}
    for site_name, cfg in sites_all.items():
        if cfg.get("skip") and not args.include_skipped:
            continue
        sites[site_name] = cfg

    base = username.strip().lower()
    if not base:
        raise ValueError("Empty username")

    usernames_to_check = [base]

    if args.variants:
        console.print(f"[bold cyan]Generating up to {args.max_variants} variations...[/bold cyan]")
        usernames_to_check = generate_username_variations(base, args.max_variants)

    all_results: Dict[str, List[Tuple[str, Optional[bool], str]]] = {}
    summary_data: List[Tuple[str, int, int]] = []
    bios_cache: Dict[str, str] = {}

    connector = aiohttp.TCPConnector(limit=args.conn_limit, ssl=False)
    sem = asyncio.Semaphore(args.concurrency)

    async with aiohttp.ClientSession(connector=connector) as session:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%",
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            total = len(usernames_to_check) * len(sites)
            task_id = progress.add_task("[cyan]Scanning...", total=total)

            for uname in usernames_to_check:
                tasks = [
                    check_username(session, sem, site_name, site_data, uname, args.proxy, args.timeout)
                    for site_name, site_data in sites.items()
                ]

                results: List[Tuple[str, Optional[bool], str]] = []
                x_exists = False

                for fut in asyncio.as_completed(tasks):
                    site, exists, url = await fut
                    results.append((site, exists, url))
                    progress.advance(task_id)

                    if exists is True and is_x_site(site, sites.get(site, {})):
                        x_exists = True

                if x_exists:
                    bio = await fetch_x_bio(session, uname, args.proxy, args.timeout)
                    if bio:
                        bios_cache[uname] = bio

                found = sum(1 for _, e, _ in results if e is True)
                summary_data.append((uname, found, len(results)))
                all_results[uname] = results

                if found > 0:
                    console.print(build_hits_table(uname, results))
                    console.print("")

                if args.show_uncertain:
                    unsure = sum(1 for _, e, _ in results if e is None)
                    if unsure:
                        console.print(build_uncertain_table(uname, results))
                        console.print("")

    print_summary(summary_data)

    if args.output:
        out_path = Path(args.output)
        if out_path.suffix.lower() == ".csv":
            with out_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Username", "Site", "Exists", "URL"])
                for uname, res in all_results.items():
                    for site, ex, url in res:
                        writer.writerow([uname, site, ex, url])
        else:
            payload = {
                uname: [{"site": s, "exists": ex, "url": url} for (s, ex, url) in res]
                for uname, res in all_results.items()
            }
            with out_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)

        console.print(f"[green]Saved to {args.output}[/green]")


def prompt_username() -> str:
    console.print("[bold cyan]Enter a username to search:[/bold cyan] ", end="")
    return input().strip()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Advanced Username Recon (better accuracy)")
    parser.add_argument("username", nargs="?", help="Username to check (optional; will prompt if omitted)")
    parser.add_argument("--variants", action="store_true")
    parser.add_argument("--max-variants", type=int, default=12)
    parser.add_argument("--proxy")
    parser.add_argument("--output")
    parser.add_argument("--sites", default="sites.json", help="Path to sites.json")

    # performance knobs
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--concurrency", type=int, default=25)
    parser.add_argument("--conn-limit", type=int, default=50)

    # behavior
    parser.add_argument("--include-skipped", action="store_true", help="Include sites marked skip:true in sites.json")
    parser.add_argument("--show-uncertain", action="store_true", help="Print uncertain sites list too")

    args = parser.parse_args()

    uname = args.username or prompt_username()
    asyncio.run(run_scan(args, uname))
    console.print("\n[bold blue]Done![/bold blue]")

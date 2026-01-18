# Username-Sniffer  
**Asynchronous Username OSINT Reconnaissance Tool (Python)**

![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![Async](https://img.shields.io/badge/async-asyncio%20%7C%20aiohttp-green.svg)
![OSINT](https://img.shields.io/badge/category-OSINT-red.svg)
![License](https://img.shields.io/badge/license-MIT-lightgrey.svg)

Username-Sniffer is a fast, asynchronous **username OSINT reconnaissance tool** written in Python.  
It scans dozens of platforms to determine whether a username exists across social networks, developer platforms, content sites, and forums.

Designed for **OSINT researchers, security analysts, investigators, and power users**.

---

## Key Features

- Asynchronous scanning with asyncio + aiohttp
- Multi-platform username discovery (40+ sites)
- HTTP status + regex-based detection
- Username variation generation
- Optional HTTP/S proxy support
- Rich terminal UI with progress tracking
- Twitter / X bio extraction (best-effort)
- Export results to JSON or CSV

---

## Supported Platforms

Includes (not exhaustive):

Twitter / X · Instagram · TikTok · GitHub · Reddit · YouTube · Twitch · Steam · LinkedIn · Telegram · Mastodon · Bluesky · Hacker News · SoundCloud · Vimeo · Substack · Pornhub · OnlyFans · Fansly · Roblox · Discord (limited)

Full list is defined in **sites.json** and can be easily extended.

---

## Requirements

- Python 3.10+
- aiohttp
- rich

Install dependencies:

```bash
pip install aiohttp rich

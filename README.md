# Username-Sniffer 🦍

**Fast Asynchronous Username OSINT Recon Tool**  
Scans 40+ platforms to discover where a username *already exists*  
(social media, gaming, adult sites, dev platforms & more)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Async](https://img.shields.io/badge/asyncio%20%7C%20aiohttp-green.svg)](https://docs.aiohttp.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Last Commit](https://img.shields.io/github/last-commit/Deathbringer98/Username-Sniffer)](https://github.com/Deathbringer98/Username-Sniffer/commits/main)
[![Open Issues](https://img.shields.io/github/issues/Deathbringer98/Username-Sniffer)](https://github.com/Deathbringer98/Username-Sniffer/issues)

Built for **OSINT investigators**, **red teamers**, **threat hunters**,  
**journalists**, and **brand protection researchers**.

---

## ✨ Key Features

- ⚡ **Blazing fast** — asyncio + aiohttp with concurrency control  
- 🔍 **40+ platforms** — social, gaming, adult, dev, and niche sites  
- 🛡️ **Smart detection** — HTTP status codes + custom regex checks  
- 🔄 **Username variations** — numbers, years, prefixes, mid-splits  
- 🌐 **Proxy support** — HTTP / SOCKS proxies  
- 🐦 **X / Twitter bio extraction** — pulls profile bio when found  
- 📊 **Rich console UI** — progress bars, tables, summaries  
- 💾 **Export results** — JSON or CSV  

> **Note:** This tool checks for *existing* profiles only.  
> It does **not** test username availability for registration.

> **Important:** Use ethically. Respect platform TOS, privacy laws, and never use this tool for harassment, stalking, or illegal activity.

---

## 🌍 Supported Platforms (40+)

### Social & Messaging
- Twitter / X  
- Instagram  
- TikTok  
- Reddit  
- LinkedIn  
- Telegram  
- Bluesky  
- Mastodon  

### Gaming & Streaming
- YouTube  
- Twitch  
- Steam  
- Roblox  

### Dev & Professional
- GitHub  
- Hacker News  

### Content & Adult
- SoundCloud  
- Vimeo  
- Substack  
- OnlyFans  
- Fansly  
- Pornhub  

**+ more** (Discord support limited, numeric IDs only)

All platforms are defined in **`sites.json`** — easy to extend or customize.

---

## 🧰 Installation

```bash
git clone https://github.com/Deathbringer98/Username-Sniffer.git
cd Username-Sniffer

pip install -r requirements.txt
# or
pip install aiohttp rich

```
## 🚀 Quick Start
## Basic scan
run this code in shell
python advanced_username_recon.py username

## With variations + output

python advanced_username_recon.py testuser123 \
  --variants \
  --max-variants 15 \
  --output results.json \
  --show-uncertain

## Using a proxy
python advanced_username_recon.py targetuser \
  --proxy http://127.0.0.1:8080

| Flag                | Description                  | Default    |
| ------------------- | ---------------------------- | ---------- |
| `username`          | Username to check            | required   |
| `--variants`        | Generate username variations | False      |
| `--max-variants N`  | Max variations to test       | 12         |
| `--proxy URL`       | HTTP/SOCKS proxy             | None       |
| `--output FILE`     | Export results (json/csv)    | None       |
| `--sites FILE`      | Custom sites.json path       | sites.json |
| `--timeout SEC`     | Request timeout              | 10         |
| `--concurrency N`   | Max concurrent tasks         | 25         |
| `--conn-limit N`    | HTTP connection pool size    | 50         |
| `--include-skipped` | Include skipped sites        | False      |
| `--show-uncertain`  | Show uncertain results       | False      |

Run:
python advanced_username_recon.py --help
for full details.

## 🖼️ Demo

<img width="784" height="837" alt="img1" src="https://github.com/user-attachments/assets/01a67bef-3860-4427-b1df-0bd8a649fa97" />


## 🤝 Contributing

PRs are welcome.

Good contributions include:

New sites in sites.json (with solid regex)

Detection accuracy improvements

Rotating user-agents or proxy lists

Performance optimizations

Additional profile metadata extraction

Fork → branch → PR
Open an issue first for large changes.

## 🧭 Roadmap

Rotating proxies & user-agents

Import WhatsMyName JSON format

Docker container

Per-site rate limiting

More profile data extraction

## 📜 License

MIT License © 2026 NightShift Gorilla 🦍

Built with ❤️ for the OSINT community.
Stay curious. Stay ethical.

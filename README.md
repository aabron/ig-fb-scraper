# Webscraper – Facebook & Instagram Business Profiles

This project gathers public data from **Facebook Pages** and **Instagram business profiles** (restaurants, bars, hospitality) and stores it in a CSV file.

## ✨ Features

* DuckDuckGo search is used for discovery so no official Facebook/Instagram APIs are required.
* Scrapes useful metadata (followers, category, bio, etc.) via:
  * [`facebook-scraper`](https://github.com/kevinzg/facebook-scraper)
  * [`instaloader`](https://instaloader.github.io/)
* Optional authenticated mode to improve data access / reduce rate-limits.
* Minimal setup – pure Python, no browser automation.

## ⚙️ Installation

```powershell
# From project root
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 🔑 Optional Authentication

### Facebook
1. Log in to Facebook in your browser.
2. Export cookies to `cookies.txt` using a browser extension (e.g. *Cookie-Editor*).
3. Supply the file path with `--fb-cookies cookies.txt`.

### Instagram
Pass a username/password with `--ig-user` / `--ig-pass`.
Instaloader saves a session file to reuse cookies and avoid 2-FA prompts.

> ⚠️ Credentials remain **local only** – the script never transmits them anywhere.

## 🚀 Usage Examples

```powershell
# Basic (unauthenticated) – searches top 10 results per platform
python scraper.py -b "Joe's Pizza" "Main Street Bar" -o output.csv

# Increase search depth & use credentials
python scraper.py -b "Blue Lagoon Resort" -o resort_profiles.csv \
     --max-results 20 --fb-cookies fb_cookies.txt \
     --ig-user myinsta --ig-pass mypassword

# Search by city & set max keyword search
python city_scraper.py -c "Detroit" --fb-cookies fb_cookies.txt
     --ig-user myinsta --ig-pass mypassword --max-per-keyword 10
```

The output `CSV` will contain combined rows from both platforms with the following columns (more may appear depending on available data):

| platform | username | full_name | followers | url | category | bio/about | ... |

## 📝 Notes & Limitations

* **Scraping policies** – Always respect the terms of service of each platform.
* Large-scale scraping may require rotating proxies or slower request rates.
* Some Facebook pages block public access; cookies or a logged-in session bypasses most blocks.
* Instagram without authentication returns limited info and is heavily rate-limited.

Feel free to adapt the code for your specific workflow! PRs welcome. 

#!/usr/bin/env python
"""
City-based Social Profile Scraper

Given a CITY name, this script will:
  1. Run DuckDuckGo searches combining hospitality keywords (restaurant, bar, cafe, …)
     with the provided city plus the target social platform (instagram.com, facebook.com).
  2. Collect profile URLs from the search results and extract usernames.
  3. Reuse scraping helpers from `scraper.py` to fetch public data for each profile.
  4. Output a consolidated CSV file.

Example:
    python city_scraper.py -c "Chicago" -o chicago_profiles.csv --max-per-keyword 15 \
        --fb-cookies fb_cookies.txt --ig-user myinsta --ig-pass mypassword

The script shares command-line flags with `scraper.py` for credentials and output.
"""

import argparse
import importlib
import sys
import random
import time
from typing import Dict, List, Optional, Set, Tuple

from tqdm import tqdm

# Dynamically import helper functions from scraper.py (same directory)
try:
    scraper = importlib.import_module("scraper")
except ModuleNotFoundError:
    print("[!] scraper.py not found in the current directory. Make sure you run this script from the project root.")
    sys.exit(1)

search_social_links = scraper.search_social_links
ensure_username_from_url = scraper.ensure_username_from_url
extract_instagram_data = scraper.extract_instagram_data
extract_facebook_data = scraper.extract_facebook_data
save_to_csv = scraper.save_to_csv

proxy_links = [
    {"http": "http://156.228.83.153:3129", "https": "http://156.228.83.153:3129"},
    {"http": "http://154.213.204.172:3129", "https": "http://154.213.204.172:3129"},
    {"http": "http://156.248.81.26:3129", "https": "http://156.248.81.26:3129"},
    {"http": "http://156.228.106.27:3129", "https": "http://156.228.106.27:3129"},
    {"http": "http://156.248.84.6:3129", "https": "http://156.248.84.6:3129"},
    {"http": "http://156.253.164.134:3129", "https": "http://156.253.164.134:3129"},
    {"http": "http://156.228.77.32:3129", "https": "http://156.228.77.32:3129"},
    {"http": "http://156.228.176.92:3129", "https": "http://156.228.176.92:3129"},
    {"http": "http://156.228.114.12:3129", "https": "http://156.228.114.12:3129"},
    {"http": "http://156.248.83.163:3129", "https": "http://156.248.83.163:3129"},
]

# ---------------- Constants ------------------
DEFAULT_KEYWORDS: Tuple[str, ...] = (
    "restaurant",
    "bar",
    "cafe",
    "pub",
    "bistro",
    "grill",
    "steakhouse",
    "brewery",
    "hotel",
)


# ---------------- profile discovery -----------------

def discover_profiles(city: str, keywords: List[str], platform: str, max_per_keyword: int) -> List[str]:
    discovered: List[str] = []
    for kw in keywords:
        query_term = f"{kw} {city}"
        urls = search_social_links(query_term, platform, max_per_keyword)
        discovered.extend(urls)

    seen: Set[str] = set()
    unique_urls: List[str] = []
    for url in discovered:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    return unique_urls


def scrape_city(city: str,
                keywords: List[str],
                fb_cookies: Optional[str],
                ig_user: Optional[str],
                ig_pass: Optional[str],
                max_per_keyword: int,
                output: str):
    import instaloader 

    # init loader
    loader = instaloader.Instaloader(request_timeout=10, max_connection_attempts=1)

    # random proxy
    proxy = random.choice(proxy_links)
    print(f"[i] Using proxy: {proxy}")
    loader.context._session.proxies.update(proxy)

    if ig_user and ig_pass:
        try:
            loader.login(ig_user, ig_pass)
            print("[i] Logged into Instagram.")
        except Exception as e:
            print(f"[!] Instagram login failed: {e}")

    rows: List[Dict[str, str]] = []
    platforms = ("instagram.com", "facebook.com")

    for platform in platforms:
        print(f"[→] Discovering {platform.split('.')[0].title()} profiles in {city}…")
        urls = discover_profiles(city, keywords, platform, max_per_keyword)
        for url in tqdm(urls, desc=f" Scraping {platform}"):
            username = ensure_username_from_url(url)
            if not username:
                continue
            try:
                data = None
                if platform == "instagram.com":
                    try:
                        data = extract_instagram_data(username, loader)
                    except instaloader.exceptions.QueryReturnedBadRequestException:
                        print("[i] Hit Instagram rate-limit – sleeping 5 min …")
                        time.sleep(300)
                    except Exception as e:
                        print(f"[!] Failed {url}: {e}")
                else:
                    try:
                        data = extract_facebook_data(username, fb_cookies)
                    except Exception as e:
                        print(f"[!] Failed {url}: {e}")

                if data:
                    rows.append(data)
            except Exception as e:
                print(f"[!] Failed {url}: {e}")

    save_to_csv(rows, output)


# ---------------- CLI ------------------------

def main():
    parser = argparse.ArgumentParser(description="Discover & scrape hospitality businesses in a given city from Facebook & Instagram.")
    parser.add_argument("-c", "--city", required=True, help="Target city (e.g., 'Chicago').")
    parser.add_argument("-o", "--output", default="city_profiles.csv", help="Output CSV file.")
    parser.add_argument("--keywords", nargs="*", help="Custom hospitality keywords (overrides defaults).")
    parser.add_argument("--max-per-keyword", type=int, default=10, help="DuckDuckGo results per keyword per platform.")
    parser.add_argument("--fb-cookies", help="Path to facebook cookies.txt file (optional).")
    parser.add_argument("--ig-user", help="Instagram username (optional).")
    parser.add_argument("--ig-pass", help="Instagram password (optional).")

    args = parser.parse_args()

    keywords = args.keywords if args.keywords else list(DEFAULT_KEYWORDS)

    scrape_city(
        city=args.city,
        keywords=keywords,
        fb_cookies=args.fb_cookies,
        ig_user=args.ig_user,
        ig_pass=args.ig_pass,
        max_per_keyword=args.max_per_keyword,
        output=args.output,
    )


if __name__ == "__main__":
    main() 
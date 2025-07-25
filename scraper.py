#!/usr/bin/env python
"""
Social Profile Scraper

Given a list of business names, this script:
1. Uses DuckDuckGo search to find public Facebook and Instagram profile URLs.
2. Scrapes each profile using dedicated libraries:
     - facebook-scraper for Facebook Pages
     - instaloader for Instagram profiles
3. Aggregates relevant details (username, url, followers, etc.)
4. Writes everything to a CSV file for analysis.

Usage (PowerShell example):
    python scraper.py -b "Joe's Pizza" "Main Street Bar" -o output.csv --max-results 15 \
        --fb-cookies facebook_cookies.txt --ig-user myinsta --ig-pass mypassword

Both Facebook cookies and Instagram credentials are optional but recommended to reduce
rate-limits and access more complete data.
"""

import argparse
import csv
from typing import Dict, List, Optional
from urllib.parse import urlparse

from ddgs import DDGS
from facebook_scraper import get_profile
import instaloader
from tqdm import tqdm


def search_social_links(business_name: str, platform: str, max_results: int = 100) -> List[str]:
    query = f"{business_name} {platform.split('.')[0]} {platform}"
    results = DDGS().text(query, max_results=max_results) or []
    urls = []
    for r in results:
        url = r.get("href") or r.get("url") or ""
        if platform in url:
            parsed = urlparse(url)
            cleaned = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            urls.append(cleaned)

    seen = set()
    unique_urls = []
    for u in urls:
        if u not in seen:
            unique_urls.append(u)
            seen.add(u)
    return unique_urls


def ensure_username_from_url(url: str) -> str:
    """Extract the first path component, which is typically the username/page slug."""
    path = urlparse(url).path
    parts = [p for p in path.split("/") if p]
    return parts[0] if parts else ""


# ---------------- ig -----------------

def extract_instagram_data(username: str, loader: instaloader.Instaloader) -> Dict[str, str]:
    profile = instaloader.Profile.from_username(loader.context, username)
    return {
        "platform": "instagram",
        "username": profile.username,
        "full_name": profile.full_name,
        "followers": profile.followers,
        "following": profile.followees,
        "posts": profile.mediacount,
        "url": f"https://www.instagram.com/{profile.username}/",
        "bio": profile.biography or "",
        "external_url": profile.external_url or "",
    }


# ---------------- facebook ------------------

def extract_facebook_data(username: str, cookies: Optional[str] = None) -> Dict[str, str]:
    profile = get_profile(username, cookies=cookies)
    return {
        "platform": "facebook",
        "username": profile.get("username") or username,
        "full_name": profile.get("name", ""),
        "followers": profile.get("followers"),
        "category": profile.get("category", ""),
        "url": profile.get("link") or f"https://www.facebook.com/{username}",
        "about": profile.get("about", ""),
        "website": profile.get("website", ""),
        "email": profile.get("email", ""),
        "phone": profile.get("phone", ""),
        "city": profile.get("city", ""),
    }


# ---------------- export to csv ----------------

def save_to_csv(rows: List[Dict[str, str]], output: str):
    if not rows:
        print("[!] No data collected, skipping CSV write.")
        return

    fieldnames = sorted({k for row in rows for k in row.keys()})
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    print(f"[✓] Saved {len(rows)} rows to {output}")


# ---------------- main ----------------------

def main():
    parser = argparse.ArgumentParser(description="Scrape Facebook & Instagram business profiles (restaurants, bars, hospitality).")
    parser.add_argument("-b", "--businesses", nargs="+", required=True, help="One or more business names to search for.")
    parser.add_argument("-o", "--output", default="social_profiles.csv", help="Destination CSV filename.")
    parser.add_argument("--fb-cookies", help="Path to facebook cookies.txt file (optional).")
    parser.add_argument("--ig-user", help="Instagram username (optional).")
    parser.add_argument("--ig-pass", help="Instagram password (optional).")
    parser.add_argument("--max-results", type=int, default=10, help="Search results per platform per business.")
    args = parser.parse_args()

    # init insta loader
    loader = instaloader.Instaloader(request_timeout=10, max_connection_attempts=1)
    if args.ig_user and args.ig_pass:
        try:
            loader.login(args.ig_user, args.ig_pass)
            print("[i] Logged in to Instagram API.")
        except Exception as e:
            print(f"[!] Instagram login failed: {e}")

    # aggregate rows
    all_rows: List[Dict[str, str]] = []

    for biz in args.businesses:
        print(f"[→] Searching social profiles for '{biz}'…")
        for platform in ("instagram.com", "facebook.com"):
            urls = search_social_links(biz, platform, args.max_results)
            for url in tqdm(urls, desc=f" {platform}"):
                username = ensure_username_from_url(url)
                if not username:
                    continue
                try:
                    if platform == "instagram.com":
                        data = extract_instagram_data(username, loader)
                    else:
                        data = extract_facebook_data(username, args.fb_cookies)
                    all_rows.append(data)
                except Exception as e:
                    print(f"[!] Failed to scrape {url}: {e}")

    save_to_csv(all_rows, args.output)


if __name__ == "__main__":
    main() 
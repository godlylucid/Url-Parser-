import requests
import itertools
import logging
import json
import time
import random
import os
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ── API Keys from Environment Variables ────────────────────────────────────────

def load_env_pairs(env_var: str) -> List[Tuple[str, str]]:
    """Load username:password pairs from environment variable."""
    value = os.getenv(env_var, "")
    if not value:
        return []
    pairs = []
    for pair in value.split(","):
        if ":" in pair:
            username, password = pair.split(":", 1)
            pairs.append((username.strip(), password.strip()))
    return pairs

def load_env_list(env_var: str) -> List[str]:
    """Load comma-separated keys from environment variable."""
    value = os.getenv(env_var, "")
    if not value:
        return []
    return [k.strip() for k in value.split(",") if k.strip()]

OXYLABS_KEYS = load_env_pairs("OXYLABS_KEYS")
SCRAPINGBEE_KEYS = load_env_list("SCRAPINGBEE_KEYS")
SCRAPERAPI_KEYS = load_env_list("SCRAPERAPI_KEYS")
ZENROWS_KEYS = load_env_list("ZENROWS_KEYS")
APIFY_KEYS = load_env_list("APIFY_KEYS")
SCRAPESTACK_KEYS = load_env_list("SCRAPESTACK_KEYS")

INPUT_FILE   = "queries.txt"
OUTPUT_FILE  = "results.txt"
GEO_LOCATION = os.getenv("GEO_LOCATION", "California,United States")
MAX_REQUESTS = int(os.getenv("MAX_REQUESTS", "5000"))


# ── Key Validator ──────────────────────────────────────────────────────────────

def is_valid_pair(username: str, password: str) -> bool:
    """Check if an Oxylabs key pair is real (not a placeholder or empty)."""
    placeholders = ("your_username", "your_password", "", None)
    return (
        username and password
        and not any(username.startswith(p) for p in placeholders if p)
        and not any(password.startswith(p) for p in placeholders if p)
        and len(username) > 3
        and len(password) > 3
    )

def is_valid_key(key: str) -> bool:
    """Check if a single API key is real (not a placeholder or empty)."""
    placeholders = (
        "your_scrapingbee", "your_scraperapi",
        "your_zenrows", "your_apify", "your_scrapestack", ""
    )
    return (
        key
        and not any(key.startswith(p) for p in placeholders)
        and len(key) > 5
    )


# ── Provider Clients ───────────────────────────────────────────────────────────

class OxylabsClient:
    def __init__(self, keys):
        self.active = [(u, p) for u, p in keys if is_valid_pair(u, p)]
        self.cycle  = itertools.cycle(self.active) if self.active else None
        self.usage  = {u: 0 for u, _ in self.active}
        self.name   = "Oxylabs"

    def scrape(self, query: str) -> Optional[dict]:
        if not self.cycle:
            return None
        auth = next(self.cycle)
        try:
            response = requests.post(
                "https://realtime.oxylabs.io/v1/queries",
                auth=auth,
                json={
                    "source":       "google_search",
                    "query":        query,
                    "geo_location": GEO_LOCATION,
                    "parse":        True,
                },
                timeout=30
            )
            if response.status_code == 200:
                self.usage[auth[0]] = self.usage.get(auth[0], 0) + 1
                return self._parse(response.json())
        except Exception as e:
            logger.error(f"[Oxylabs] Error: {e}")
        return None

    def _parse(self, data: dict) -> Optional[dict]:
        try:
            organics = data["results"][0]["content"]["results"]["organic"]
            return {
                "provider": self.name,
                "organic": [
                    {
                        "title": i.get("title", ""),
                        "url":   i.get("url",   ""),
                        "desc":  i.get("desc",  ""),
                    }
                    for i in organics
                ]
            }
        except (KeyError, IndexError, TypeError):
            return None


class ScrapingBeeClient:
    def __init__(self, keys):
        self.active = [k for k in keys if is_valid_key(k)]
        self.cycle  = itertools.cycle(self.active) if self.active else None
        self.usage  = {k: 0 for k in self.active}
        self.name   = "ScrapingBee"

    def scrape(self, query: str) -> Optional[dict]:
        if not self.cycle:
            return None
        key = next(self.cycle)
        try:
            response = requests.get(
                "https://app.scrapingbee.com/api/v1/",
                params={
                    "api_key":  key,
                    "url":      f"https://www.google.com/search?q={requests.utils.quote(query)}",
                    "render_js": "false",
                    "extract_rules": json.dumps({
                        "titles": {"selector": "h3",               "type": "list"},
                        "links":  {"selector": "a[href]",          "type": "list", "output": "@href"},
                        "descs":  {"selector": ".VwiC3b, .IsZvec", "type": "list"},
                    }),
                },
                timeout=30
            )
            if response.status_code == 200:
                self.usage[key] = self.usage.get(key, 0) + 1
                return self._parse(response.json())
        except Exception as e:
            logger.error(f"[ScrapingBee] Error: {e}")
        return None

    def _parse(self, data: dict) -> Optional[dict]:
        try:
            titles = data.get("titles", [])
            links  = [l for l in data.get("links", []) if l and l.startswith("http") and "google" not in l]
            descs  = data.get("descs", [])
            organic = [
                {
                    "title": titles[i] if i < len(titles) else "",
                    "url":   links[i],
                    "desc":  descs[i]  if i < len(descs)  else "",
                }
                for i in range(min(len(links), 10))
            ]
            return {"provider": self.name, "organic": organic} if organic else None
        except Exception:
            return None


class ScraperAPIClient:
    def __init__(self, keys):
        self.active = [k for k in keys if is_valid_key(k)]
        self.cycle  = itertools.cycle(self.active) if self.active else None
        self.usage  = {k: 0 for k in self.active}
        self.name   = "ScraperAPI"

    def scrape(self, query: str) -> Optional[dict]:
        if not self.cycle:
            return None
        key = next(self.cycle)
        try:
            response = requests.get(
                "http://api.scraperapi.com/",
                params={
                    "api_key":   key,
                    "url":       f"https://www.google.com/search?q={requests.utils.quote(query)}",
                    "autoparse": "true",
                },
                timeout=30
            )
            if response.status_code == 200:
                self.usage[key] = self.usage.get(key, 0) + 1
                return self._parse(response.json())
        except Exception as e:
            logger.error(f"[ScraperAPI] Error: {e}")
        return None

    def _parse(self, data: dict) -> Optional[dict]:
        try:
            organic = [
                {
                    "title": i.get("title",   ""),
                    "url":   i.get("link",    ""),
                    "desc":  i.get("snippet", ""),
                }
                for i in data.get("organic_results", [])
            ]
            return {"provider": self.name, "organic": organic} if organic else None
        except Exception:
            return None


class ZenRowsClient:
    def __init__(self, keys):
        self.active = [k for k in keys if is_valid_key(k)]
        self.cycle  = itertools.cycle(self.active) if self.active else None
        self.usage  = {k: 0 for k in self.active}
        self.name   = "ZenRows"

    def scrape(self, query: str) -> Optional[dict]:
        if not self.cycle:
            return None
        key = next(self.cycle)
        try:
            response = requests.get(
                "https://api.zenrows.com/v1/",
                params={
                    "apikey":    key,
                    "url":       f"https://www.google.com/search?q={requests.utils.quote(query)}",
                    "autoparse": "true",
                    "js_render": "false",
                },
                timeout=30
            )
            if response.status_code == 200:
                self.usage[key] = self.usage.get(key, 0) + 1
                return self._parse(response.json())
        except Exception as e:
            logger.error(f"[ZenRows] Error: {e}")
        return None

    def _parse(self, data: dict) -> Optional[dict]:
        try:
            organic = [
                {
                    "title": i.get("title",       ""),
                    "url":   i.get("url",         ""),
                    "desc":  i.get("description", ""),
                }
                for i in data.get("organic_results", [])
            ]
            return {"provider": self.name, "organic": organic} if organic else None
        except Exception:
            return None


class ApifyClient:
    def __init__(self, keys):
        self.active = [k for k in keys if is_valid_key(k)]
        self.cycle  = itertools.cycle(self.active) if self.active else None
        self.usage  = {k: 0 for k in self.active}
        self.name   = "Apify"

    def scrape(self, query: str) -> Optional[dict]:
        if not self.cycle:
            return None
        key = next(self.cycle)
        try:
            run_resp = requests.post(
                "https://api.apify.com/v2/acts/apify~google-search-scraper/runs",
                headers={"Authorization": f"Bearer {key}"},
                json={
                    "queries":          query,
                    "maxPagesPerQuery": 1,
                    "resultsPerPage":   10,
                    "languageCode":     "en",
                    "countryCode":      "us",
                },
                timeout=60
            )
            if run_resp.status_code not in (200, 201):
                return None

            run_id = run_resp.json()["data"]["id"]

            for _ in range(12):
                time.sleep(5)
                status_resp = requests.get(
                    f"https://api.apify.com/v2/acts/apify~google-search-scraper/runs/{run_id}",
                    headers={"Authorization": f"Bearer {key}"},
                    timeout=30
                )
                status = status_resp.json()["data"]["status"]
                if status == "SUCCEEDED":
                    break
                elif status in ("FAILED", "ABORTED"):
                    return None

            dataset_id = status_resp.json()["data"]["defaultDatasetId"]
            items_resp = requests.get(
                f"https://api.apify.com/v2/datasets/{dataset_id}/items",
                headers={"Authorization": f"Bearer {key}"},
                timeout=30
            )
            if items_resp.status_code == 200:
                self.usage[key] = self.usage.get(key, 0) + 1
                return self._parse(items_resp.json())
        except Exception as e:
            logger.error(f"[Apify] Error: {e}")
        return None

    def _parse(self, data: list) -> Optional[dict]:
        try:
            organic = [
                {
                    "title": i.get("title",       ""),
                    "url":   i.get("url",         ""),
                    "desc":  i.get("description", ""),
                }
                for page in data
                for i in page.get("organicResults", [])
            ]
            return {"provider": self.name, "organic": organic} if organic else None
        except Exception:
            return None


class ScrapeStackClient:
    def __init__(self, keys):
        self.active = [k for k in keys if is_valid_key(k)]
        self.cycle  = itertools.cycle(self.active) if self.active else None
        self.usage  = {k: 0 for k in self.active}
        self.name   = "Scrapestack"

    def scrape(self, query: str) -> Optional[dict]:
        if not self.cycle:
            return None
        key = next(self.cycle)
        try:
            response = requests.get(
                "http://api.scrapestack.com/scrape",
                params={
                    "access_key": key,
                    "url":        f"https://www.google.com/search?q={requests.utils.quote(query)}",
                    "render_js":  0,
                },
                timeout=30
            )
            if response.status_code == 200:
                self.usage[key] = self.usage.get(key, 0) + 1
                return self._parse(response.text)
        except Exception as e:
            logger.error(f"[Scrapestack] Error: {e}")
        return None

    def _parse(self, html: str) -> Optional[dict]:
        try:
            import re
            urls    = re.findall(r'href="(https?://[^"&]+)"', html)
            clean   = [u for u in urls if "google" not in u and "youtube" not in u]
            organic = [{"title": "", "url": u, "desc": ""} for u in clean[:10]]
            return {"provider": self.name, "organic": organic} if organic else None
        except Exception:
            return None


# ── Multi-Provider Scraper ─────────────────────────────────────────────────────

class MultiProviderScraper:
    def __init__(self):
        self.request_count = 0

        all_clients = [
            OxylabsClient(OXYLABS_KEYS),
            ScrapingBeeClient(SCRAPINGBEE_KEYS),
            ScraperAPIClient(SCRAPERAPI_KEYS),
            ZenRowsClient(ZENROWS_KEYS),
            ApifyClient(APIFY_KEYS),
            ScrapeStackClient(SCRAPESTACK_KEYS),
        ]

        # Only keep providers that have at least 1 valid key
        self.providers = [c for c in all_clients if c.active]

        if not self.providers:
            raise ValueError(
                "\n[ERROR] No valid API keys found in any provider!\n"
                "Please configure your .env file with at least one API key.\n"
                "See .env.example for the correct format.\n"
            )

        self._provider_cycle = itertools.cycle(self.providers)

        print("\n" + "="*60)
        print("  PROVIDER STATUS")
        print("="*60)
        for c in all_clients:
            status = f"✓  {len(c.active)} key(s) active" if c.active else "✗  skipped (no keys)"
            print(f"  {c.name:<15} {status}")
        print("="*60)

    def scrape(self, query: str) -> Optional[dict]:
        if self.request_count >= MAX_REQUESTS:
            logger.warning("Max request limit reached.")
            return None

        for _ in range(len(self.providers)):
            provider = next(self._provider_cycle)
            logger.info(f"Trying: {provider.name}")
            result = provider.scrape(query)
            if result:
                self.request_count += 1
                return result
            logger.warning(f"{provider.name} failed, rotating...")

        logger.error("All providers failed for this query.")
        return None

    def print_summary(self):
        print("\n" + "="*60)
        print("  PROVIDER USAGE SUMMARY")
        print("="*60)
        for p in self.providers:
            total = sum(p.usage.values())
            print(f"\n  [{p.name}] — {total} request(s)")
            for key, count in p.usage.items():
                short = key[:22] + "..." if len(key) > 22 else key
                bar   = "█" * min(count, 20) + "░" * max(0, 20 - min(count, 20))
                print(f"    {short:<26} {bar} {count}")
        print("\n" + "="*60)
        print(f"  GRAND TOTAL: {self.request_count} requests used")
        print("="*60 + "\n")


# ── File Helpers ───────────────────────────────────────────────────────────────

def load_queries_from_file(filepath: str) -> List[str]:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(
            f"\n[ERROR] '{filepath}' not found!\n"
            "Create a queries.txt file with one dork/query per line.\n"
        )
    queries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                queries.append(line)
    if not queries:
        raise ValueError(f"\n[ERROR] '{filepath}' is empty! Add at least one query.\n")
    logger.info(f"Loaded {len(queries)} queries from '{filepath}'")
    return queries


def save_results_to_file(results: List[dict], filepath: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success   = sum(1 for r in results if r["result"] is not None)
    failed    = len(results) - success

    with open(Path(filepath), "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("     MULTI-PROVIDER SCRAPER RESULTS\n")
        f.write("=" * 60 + "\n")
        f.write(f"Generated : {timestamp}\n")
        f.write(f"Total     : {len(results)} queries\n")
        f.write(f"Success   : {success}\n")
        f.write(f"Failed    : {failed}\n")
        f.write("=" * 60 + "\n\n")

        for idx, entry in enumerate(results, 1):
            query    = entry.get("query",  "N/A")
            result   = entry.get("result")
            provider = result.get("provider", "N/A") if result else "N/A"

            f.write(f"[{idx}] Query   : {query}\n")
            f.write(f"     Provider: {provider}\n")
            f.write("-" * 40 + "\n")

            if result is None:
                f.write("  STATUS: FAILED\n")
            else:
                organics = result.get("organic", [])
                f.write(f"  Results ({len(organics)} found):\n\n")
                for i, item in enumerate(organics, 1):
                    f.write(f"  {i}. {item.get('title', 'No title')}\n")
                    f.write(f"     URL : {item.get('url',   'N/A')}\n")
                    f.write(f"     Desc: {item.get('desc',  'N/A')}\n\n")

            f.write("\n")

    logger.info(f"Results saved to '{filepath}'")
    print(f"\n{'='*60}")
    print(f"  Done! {success}/{len(results)} successful")
    print(f"  Saved to: {filepath}")
    print(f"{'='*60}\n")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*60)
    print("     MULTI-PROVIDER DORK SCRAPER")
    print("     Oxylabs · ScrapingBee · ScraperAPI")
    print("     ZenRows · Apify · Scrapestack")
    print("="*60)

    scraper = MultiProviderScraper()
    queries = load_queries_from_file(INPUT_FILE)

    print(f"\n  Queries: {len(queries)}")
    print(f"  Output : {OUTPUT_FILE}")
    print(f"  Cap    : {MAX_REQUESTS} requests")
    print("=" * 60 + "\n")

    all_results = []

    for i, query in enumerate(queries, 1):
        if scraper.request_count >= MAX_REQUESTS:
            logger.warning("Request cap reached. Stopping early.")
            break

        print(f"[{i}/{len(queries)}] {query}")

        result = scraper.scrape(query)
        all_results.append({"query": query, "result": result})

        delay = random.uniform(1.5, 3.0)
        logger.info(f"Waiting {delay:.1f}s...")
        time.sleep(delay)

    save_results_to_file(all_results, OUTPUT_FILE)
    scraper.print_summary()


if __name__ == "__main__":
    main()

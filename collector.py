from datetime import datetime, timezone
from typing import List, Dict, Any
import feedparser
import requests

from logger_setup import setup_logger
from storage import ThreatStorage

logger = setup_logger("collector")


class ThreatCollector:
    def __init__(self, rss_feeds: Dict[str, str]):
        self.rss_feeds = rss_feeds

    def fetch_all(self) -> List[Dict[str, Any]]:
        all_entries = []
        all_entries.extend(self._fetch_rss_feeds())
        all_entries.extend(self._fetch_cisa_kev())
        all_entries.extend(self._fetch_nvd())
        logger.info(f"Totalt hämtade poster innan deduplicering: {len(all_entries)}")
        return all_entries

    def _fetch_rss_feeds(self) -> List[Dict[str, Any]]:
        entries = []
        for source_name, url in self.rss_feeds.items():
            try:
                logger.info(f"Hämtar RSS: {source_name}")
                parsed = feedparser.parse(url)
                for entry in parsed.entries:
                    published = entry.get("published") or entry.get("updated") or ""
                    entries.append({
                        "title": entry.get("title", "Ingen titel"),
                        "source_name": source_name,
                        "summary": entry.get("summary", entry.get("description", "Ingen beskrivning")),
                        "published": published,
                        "link": entry.get("link", ""),
                        "fetched_at": datetime.now(timezone.utc).isoformat()
                    })
                logger.info(f"  → {len(parsed.entries)} poster från {source_name}")
            except Exception as e:
                logger.error(f"Kunde inte hämta {source_name}: {e}")
        return entries

    def _fetch_cisa_kev(self) -> List[Dict[str, Any]]:
        entries = []
        url = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
        try:
            logger.info("Hämtar CISA KEV")
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("vulnerabilities", []):
                cve_id = item.get("cveID", "")
                entries.append({
                    "title": f"[{cve_id}] {item.get('vulnerabilityName', '')}",
                    "source_name": "CISA KEV",
                    "summary": (
                        f"Aktivt utnyttjad sårbarhet. {item.get('shortDescription', '')} "
                        f"Krävd åtgärd: {item.get('requiredAction', 'Ej angiven')}"
                    ),
                    "published": item.get("dateAdded", ""),
                    "link": f"https://www.cisa.gov/known-exploited-vulnerabilities?search_api_fulltext={cve_id}",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "cve_id": cve_id
                })
            logger.info(f"  → {len(data.get('vulnerabilities', []))} poster från CISA KEV")
        except Exception as e:
            logger.error(f"Kunde inte hämta CISA KEV: {e}")
        return entries

    def _fetch_nvd(self, results_per_page: int = 20) -> List[Dict[str, Any]]:
        entries = []
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        try:
            logger.info("Hämtar NIST NVD")
            headers = {"User-Agent": "ThreatIntelPipeline/1.0"}
            resp = requests.get(url, params={"resultsPerPage": results_per_page}, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for item in data.get("vulnerabilities", []):
                cve = item.get("cve", {})
                cve_id = cve.get("id", "")
                descriptions = cve.get("descriptions", [])
                summary = next((d["value"] for d in descriptions if d.get("lang") == "en"), "Ingen beskrivning")
                entries.append({
                    "title": f"[{cve_id}] Ny sårbarhet (NIST NVD)",
                    "source_name": "NIST NVD",
                    "summary": summary,
                    "published": cve.get("published", "")[:10],
                    "link": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                    "cve_id": cve_id
                })
            logger.info(f"  → {len(data.get('vulnerabilities', []))} poster från NIST NVD")
        except Exception as e:
            logger.error(f"Kunde inte hämta NIST NVD: {e}")
        return entries


if __name__ == "__main__":
    # Standardflöden som skickas till klassen
    feeds = {
        "The Hacker News": "https://thehackernews.com/feeds/posts/default",
        "BleepingComputer": "https://www.bleepingcomputer.com/feed/"
    }

    collector = ThreatCollector(rss_feeds=feeds)
    storage = ThreatStorage()

    print("🚀 Startar insamling från RSS, CISA KEV och NIST NVD...")
    entries = collector.fetch_all()

    for entry in entries:
        storage.insert_entry(
            title=entry["title"],
            content=entry["summary"],
            link=entry["link"],
            source=entry["source_name"],
            published=entry["published"]
        )
    
    print(f"✅ Klart! Sparade {len(entries)} poster i databasen.")
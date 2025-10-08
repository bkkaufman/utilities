import feedparser
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------

MAX_RESULTS = 200
SEARCH_DAYS = 90

'''
SSRN feed search configuration.

SSRN (Social Science Research Network) provides open-access RSS feeds
for many research areas, including economics, law, and emerging technology.
There is no public REST API, but metadata and abstracts can be retrieved
through these feeds.

The link below uses SSRN's Technology or Artificial Intelligence topic feeds.
You can replace it with other category feeds by visiting:
https://papers.ssrn.com/sol3/rss/rss_feeds.cfm

That combination will:
- Retrieve the most recent papers in AI, ML, or technology-related categories.
- Mirror the arXiv fetch pattern for comparison in output.
- Require no authentication or API key.

Example RSS feed URLs:
  - https://papers.ssrn.com/sol3/rss/Artificial_Intelligence.rss
  - https://papers.ssrn.com/sol3/rss/Information_Technology.rss
  - https://papers.ssrn.com/sol3/rss/Machine_Learning.rss
'''

SSRN_FEEDS = [
    "https://papers.ssrn.com/sol3/rss/Artificial_Intelligence.rss",
    "https://papers.ssrn.com/sol3/rss/Machine_Learning.rss",
    "https://papers.ssrn.com/sol3/rss/Information_Technology.rss"
]


# ---------------------------------------
# CLASS DEFINITION
# ---------------------------------------

class SSRNSearch:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir

    def fetch_results(self):
        week_ago = datetime.now() - timedelta(days=SEARCH_DAYS)
        results = []

        for feed_url in SSRN_FEEDS:
            print(f"Fetching SSRN feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            if not feed.entries:
                continue

            for entry in feed.entries:
                try:
                    published = None
                    if hasattr(entry, "published_parsed"):
                        published = datetime(*entry.published_parsed[:6])
                        if published < week_ago:
                            continue

                    results.append({
                        "title": entry.get("title", "N/A"),
                        "authors": entry.get("author", "N/A"),
                        "published": published.date() if published else None,
                        "link": entry.get("link", ""),
                        "summary": entry.get("summary", "No abstract available.")
                    })

                    print(f"Found: {entry.get('title', 'N/A')}")
                    if len(results) >= MAX_RESULTS:
                        break
                except Exception:
                    continue

            if len(results) >= MAX_RESULTS:
                break

        return results

import requests
from datetime import datetime, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET
import time

# ---------------------------------------
# CONFIGURATION CONSTANTS
# ---------------------------------------

MAX_RESULTS_PER_QUERY = 100  # Max per individual query
SEARCH_DAYS = 120
DELAY_BETWEEN_REQUESTS = 3  # seconds
MAX_RETRIES = 3

'''
ArXiv codes for search.

cs.AI	Artificial Intelligence: General AI research (planning, reasoning, symbolic AI, etc.)
cs.LG	Machine Learning: Core ML theory, algorithms, optimization, training techniques
cs.CL	Computation and Language: NLP, LLMs, transformers, text generation, etc
cs.CV	Computer Vision
cs.HC	Human–Computer Interaction
cs.RO	Robotics
cs.IR	Information Retrieval
cs.DC	Distributed, Parallel, and Cluster Computing (relevant for scaling)
stat.ML	Statistics – Machine Learning (Bayesian, probabilistic, etc.)
'''

# Split into multiple smaller queries to get more total results
ARXIV_QUERIES = [
    # Query 1: Foundation models and LLMs
    '("foundation model" OR "large language model" OR "LLM") AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)',

    # Query 2: Agentic systems
    '("agentic" OR "multi-agent" OR "autonomous agent") AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.DC)',

    # Query 3: RAG and retrieval
    '("RAG" OR "retrieval augmented" OR "retrieval" OR "information retrieval") AND (cat:cs.IR OR cat:cs.CL OR cat:cs.AI)',

    # Query 4: Medical AI
    '("pharmacovigilance" OR "medical AI" OR "clinical AI" OR "healthcare AI") AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL)',

    # Query 5: Autonomous systems and robotics
    '("autonomous system" OR "autonomous agent") AND (cat:cs.RO OR cat:cs.AI OR cat:cs.DC)',
]


# ---------------------------------------
# CLASS DEFINITION
# ---------------------------------------

class ArxivSearch:
    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.base_url = "https://export.arxiv.org/api/query"
        self.seen_titles = set()  # Track duplicates across queries

    def _fetch_page(self, query: str, start: int, max_results: int, retry_count: int = 0):
        """Directly query the Arxiv API for a given offset range with retry logic."""
        params = {
            "search_query": query,
            "start": start,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            if not response.text or len(response.text.strip()) == 0:
                return None

            return response.text

        except requests.exceptions.Timeout:
            if retry_count < MAX_RETRIES:
                print(f"  Timeout at offset {start}. Retrying ({retry_count + 1}/{MAX_RETRIES})...")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                return self._fetch_page(query, start, max_results, retry_count + 1)
            return None

        except requests.exceptions.RequestException as e:
            if retry_count < MAX_RETRIES:
                print(f"  Error: {e}. Retrying ({retry_count + 1}/{MAX_RETRIES})...")
                time.sleep(DELAY_BETWEEN_REQUESTS)
                return self._fetch_page(query, start, max_results, retry_count + 1)
            return None

    def _fetch_single_query(self, query: str, query_num: int, total_queries: int):
        """Fetch results for a single query."""
        print(f"\n{'=' * 70}")
        print(f"Query {query_num}/{total_queries}: {query[:80]}...")
        print(f"{'=' * 70}")

        cutoff_date = datetime.now() - timedelta(days=SEARCH_DAYS)
        papers = []

        # Fetch up to MAX_RESULTS_PER_QUERY for this query
        start = 0
        page_size = 50  # Smaller page size for more granular progress

        while start < MAX_RESULTS_PER_QUERY:
            print(f"  Fetching results {start + 1} to {start + page_size}...")

            xml_data = self._fetch_page(query, start, page_size)
            if xml_data is None:
                print(f"  No more results at offset {start}")
                break

            try:
                root = ET.fromstring(xml_data)
            except ET.ParseError as e:
                print(f"  XML parsing error: {e}")
                break

            entries = root.findall("{http://www.w3.org/2005/Atom}entry")

            if not entries:
                print(f"  No entries found at offset {start}")
                break

            for entry in entries:
                try:
                    title = entry.findtext("{http://www.w3.org/2005/Atom}title", "N/A")
                    if title != "N/A":
                        title = title.strip().replace('\n', ' ')

                    # Skip duplicates
                    if title in self.seen_titles:
                        continue

                    published_str = entry.findtext("{http://www.w3.org/2005/Atom}published")
                    if not published_str:
                        continue

                    published_dt = datetime.strptime(published_str, "%Y-%m-%dT%H:%M:%SZ")
                    if published_dt < cutoff_date:
                        continue

                    authors = [
                        a.findtext("{http://www.w3.org/2005/Atom}name")
                        for a in entry.findall("{http://www.w3.org/2005/Atom}author")
                        if a.findtext("{http://www.w3.org/2005/Atom}name")
                    ]

                    pdf_url = next(
                        (link.attrib["href"] for link in entry.findall("{http://www.w3.org/2005/Atom}link")
                         if link.attrib.get("title") == "pdf"),
                        None
                    )

                    summary = entry.findtext("{http://www.w3.org/2005/Atom}summary", "")
                    if summary:
                        summary = summary.strip()

                    categories = [
                        cat.attrib["term"]
                        for cat in entry.findall("{http://arxiv.org/schemas/atom}category")
                        if "term" in cat.attrib
                    ]

                    papers.append({
                        "title": title,
                        "authors": authors,
                        "published": published_dt.date(),
                        "categories": categories,
                        "pdf_url": pdf_url,
                        "summary": summary
                    })

                    self.seen_titles.add(title)
                    print(f"    Found: {title[:70]}...")

                except Exception as e:
                    continue

            # Move to next page
            start += page_size

            # If we got fewer results than page_size, we've reached the end
            if len(entries) < page_size:
                break

            time.sleep(DELAY_BETWEEN_REQUESTS)

        print(f"  Subtotal for this query: {len(papers)} papers")
        return papers

    def fetch_results(self):
        """Fetch results from multiple queries and combine them."""
        all_papers = []

        print(f"\nSearching arXiv with {len(ARXIV_QUERIES)} different queries")
        print(f"Date range: Last {SEARCH_DAYS} days")
        print(f"Max results per query: {MAX_RESULTS_PER_QUERY}\n")

        for i, query in enumerate(ARXIV_QUERIES, 1):
            papers = self._fetch_single_query(query, i, len(ARXIV_QUERIES))
            all_papers.extend(papers)

            print(f"  Running total: {len(all_papers)} unique papers")

            # Delay between queries
            if i < len(ARXIV_QUERIES):
                time.sleep(DELAY_BETWEEN_REQUESTS)

        # Sort by publication date (newest first)
        all_papers.sort(key=lambda x: x['published'], reverse=True)

        print(f"\n{'=' * 70}")
        print(f"TOTAL PAPERS FOUND: {len(all_papers)}")
        print(f"{'=' * 70}\n")

        return all_papers
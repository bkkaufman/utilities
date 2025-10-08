import arxiv
from datetime import datetime, timedelta
import os
from pathlib import Path

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

MAX_RESULTS = 200
SEARCH_DAYS = 90

ARXIV_QUERY = '("foundation model" OR "agentic" OR "multi-agent" OR "autonomous system" OR "RAG" OR "retrieval" OR "pharmacovigilance" OR "medical AI") AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV OR cat:cs.HC OR cat:cs.IR OR cat:cs.DC OR cat:stat.ML)'

# Create a client
client = arxiv.Client()
week_ago = datetime.now() - timedelta(days=SEARCH_DAYS)

# Prepare markdown output
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = output_dir / f"arxiv_results_{timestamp}.md"
papers_found = []

print(f"Searching arXiv for papers published after {week_ago.date()}...")

# Create search with MAX_RESULTS (not paginated manually)
search = arxiv.Search(
    query=ARXIV_QUERY,
    max_results=MAX_RESULTS,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

# Fetch all results at once
try:
    results = client.results(search)

    for paper in results:
        # Filter by date
        if paper.published.replace(tzinfo=None) > week_ago:
            papers_found.append(paper)
            print(f"Found ({len(papers_found)}): {paper.title}")

        # Stop if we've collected MAX_RESULTS papers
        if len(papers_found) >= MAX_RESULTS:
            break

except Exception as e:
    print(f"Error during search: {e}")

# Write to markdown file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"# arXiv Search Results\n\n")
    f.write(f"**Search Query:** `{ARXIV_QUERY}`\n\n")
    f.write(f"**Date Range:** Papers published after {week_ago.date()}\n\n")
    f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
    f.write(f"**Total Papers Found:** {len(papers_found)}\n\n")
    f.write("---\n\n")

    for i, paper in enumerate(papers_found, 1):
        f.write(f"## {i}. {paper.title}\n\n")
        f.write(f"**Authors:** {', '.join(author.name for author in paper.authors)}\n\n")
        f.write(f"**Published:** {paper.published.date()}\n\n")
        f.write(f"**Categories:** {', '.join(paper.categories)}\n\n")
        f.write(f"**PDF:** [{paper.pdf_url}]({paper.pdf_url})\n\n")
        f.write(f"**Abstract:**\n\n{paper.summary}\n\n")
        f.write("---\n\n")

print(f"\nResults saved to: {output_file}")
print(f"Total papers: {len(papers_found)}")
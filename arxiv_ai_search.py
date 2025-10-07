import arxiv
from datetime import datetime, timedelta
import os
from pathlib import Path

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

MAX_RESULTS=100
ARXIV_QUERY="cat:cs.AI OR cat:cs.LG OR cat:cs.CL"
SEARCH_DAYS=60


# Create a client.
client = arxiv.Client()

# Search for recent AI/ML papers
search = arxiv.Search(
    query=ARXIV_QUERY,
    max_results=MAX_RESULTS,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

# Fetch and display abstracts that have been published in the last week.
week_ago = datetime.now() - timedelta(days=SEARCH_DAYS)

# Prepare markdown output
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = output_dir / f"arxiv_results_{timestamp}.md"

papers_found = []

for paper in client.results(search):
    if paper.published.replace(tzinfo=None) > week_ago:
        papers_found.append(paper)
        print(f"Found: {paper.title}")

# Write to markdown file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"# arXiv Search Results\n\n")
    f.write(f"**Search Query:** `cat:cs.AI OR cat:cs.LG OR cat:cs.CL`\n\n")
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


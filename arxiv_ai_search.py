import arxiv
from datetime import datetime, timedelta
import os
from pathlib import Path

# Create output directory if it doesn't exist
output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

MAX_RESULTS=200
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

That combination will:
- Catch LLM papers (cs.CL)
- Include reasoning and planning (cs.AI)
- Pull in applied ML and foundation model training (cs.LG, stat.ML)
- Grab systems and multi-agent work (cs.DC, cs.RO)
- Surface user experience and agentic interface work (cs.HC)
- Bring in retrieval and hybrid RAG systems (cs.IR)
'''

# ARXIV_QUERY="cat:cs.AI OR cat:cs.LG OR cat:cs.CL"
ARXIV_QUERY = '("foundation model" OR "agentic" OR "multi-agent" OR "autonomous system" OR "RAG" OR "retrieval" OR "pharmacovigilance" OR "medical AI") AND (cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV OR cat:cs.HC OR cat:cs.IR OR cat:cs.DC OR cat:stat.ML)'

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


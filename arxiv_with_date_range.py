from datetime import datetime, timedelta

search = arxiv.Search(
    query="cat:cs.LG",
    max_results=100,
    sort_by=arxiv.SortCriterion.SubmittedDate
)

# Only show papers from last 7 days
week_ago = datetime.now() - timedelta(days=7)
for paper in search.results():
    if paper.published.replace(tzinfo=None) > week_ago:
        print(f"{paper.title}\n{paper.summary[:200]}...\n")
from datetime import datetime
from pathlib import Path
from searches.arxiv_search import ArxivSearch
from searches.firecrawl_ssrn_search import FirecrawlSSRNSearch
import os


def write_results_markdown(arxiv_results, ssrn_results, output_path: Path):
    """Write combined results to markdown file."""
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# AI Search Results\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("---\n\n")

            # arXiv Section
            f.write(f"## arXiv Results (found {len(arxiv_results)})\n\n")
            for i, paper in enumerate(arxiv_results, 1):
                f.write(f"### {i}. {paper['title']}\n\n")
                f.write(f"**Authors:** {', '.join(paper['authors'])}\n\n")
                f.write(f"**Published:** {paper['published']}\n\n")
                f.write(f"**Categories:** {', '.join(paper['categories'])}\n\n")
                if paper.get('pdf_url'):
                    f.write(f"**PDF:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n")
                f.write(f"**Abstract:**\n\n{paper['summary']}\n\n")
                f.write("---\n\n")

            # SSRN Section
            f.write(f"## SSRN Results (found {len(ssrn_results)})\n\n")
            for i, paper in enumerate(ssrn_results, 1):
                f.write(f"### {i}. {paper['title']}\n\n")
                f.write(f"**Authors:** {paper['authors']}\n\n")
                if paper.get('published'):
                    f.write(f"**Published:** {paper['published']}\n\n")
                if paper.get('journal'):
                    f.write(f"**Journal:** {paper['journal']}\n\n")
                if paper.get('doi'):
                    f.write(f"**DOI:** [https://doi.org/{paper['doi']}](https://doi.org/{paper['doi']})\n\n")
                if paper.get('link'):
                    f.write(f"**Link:** [{paper['link']}]({paper['link']})\n\n")
                f.write(f"**Abstract:**\n\n{paper['summary']}\n\n")
                f.write("---\n\n")

        # Verify file was created
        if output_path.exists():
            file_size = output_path.stat().st_size
            print(f"\n✅ File successfully created!")
            print(f"   Path: {output_path}")
            print(f"   Size: {file_size:,} bytes")
            return True
        else:
            print(f"\n❌ ERROR: File was not created at {output_path}")
            return False

    except Exception as e:
        print(f"\n❌ ERROR writing file: {e}")
        return False


def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"

    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Output directory exists: {output_dir.exists()}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"ai_results_{timestamp}.md"

    print(f"Target output file: {output_file.absolute()}\n")

    # Fetch arXiv results
    arxiv_search = ArxivSearch(output_dir)
    print("=" * 70)
    print("FETCHING ARXIV RESULTS")
    print("=" * 70)
    arxiv_results = arxiv_search.fetch_results()
    print(f"\narXiv: {len(arxiv_results)} papers found.\n")

    # Fetch SSRN results
    firecrawl_ssrn_search = FirecrawlSSRNSearch(output_dir)
    print("=" * 70)
    print("FETCHING SSRN RESULTS")
    print("=" * 70)
    ssrn_results = firecrawl_ssrn_search.fetch_results()
    print(f"\nSSRN: {len(ssrn_results)} papers found.\n")

    # Write combined results
    print("=" * 70)
    print("WRITING COMBINED RESULTS")
    print("=" * 70)
    success = write_results_markdown(arxiv_results, ssrn_results, output_file)

    if success:
        # Double-check the file is readable
        try:
            with open(output_file, 'r') as f:
                content = f.read()
                print(f"   Content preview: {len(content)} characters")
                print(f"   First line: {content.split(chr(10))[0]}")
        except Exception as e:
            print(f"   ⚠️  Warning: Could not read back file: {e}")


if __name__ == "__main__":
    main()
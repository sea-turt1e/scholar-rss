from arxiv_fetcher import ArxivFetcher
from paper_summarizer import PaperSummarizer

# arXiv APIから論文を取得
fetcher = ArxivFetcher(delay=3.0)
papers = fetcher.fetch_ai_papers(max_results=5)

# 論文を要約
summarizer = PaperSummarizer()
summaries = summarizer.summarize_papers(papers)

# 結果を表示
for summary in summaries:
    print(f"Title: {summary.title}")
    print(f"Summary: {summary.summary}")
    print("---")

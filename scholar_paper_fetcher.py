import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from google_scholar_fetcher import EfficientScholarFetcher


@dataclass
class ScholarPaper:
    """Google Scholarから取得した論文のデータクラス"""

    id: str
    title: str
    authors: List[str]
    year: Optional[int]
    citations: int
    link: str
    pdf_link: Optional[str]
    snippet: str
    fetched_date: str


class ScholarPaperFetcher:
    """Google Scholar Fetcherのラッパークラス"""

    def __init__(self, api_key: str, cache_dir: str = "./scholar_cache"):
        """
        Args:
            api_key: SerpApiのAPIキー
            cache_dir: キャッシュディレクトリ
        """
        self.fetcher = EfficientScholarFetcher(api_key, cache_dir)

    def fetch_papers(self, force: bool = False, prefer_recent: bool = False, max_papers: int = 1) -> List[ScholarPaper]:
        """
        Google Scholarから論文を取得

        Args:
            force: 今日既に取得済みでも強制的に取得するか
            prefer_recent: 最新論文を優先するか

        Returns:
            ScholarPaperのリスト
        """
        # Google Scholar Fetcherから論文を取得
        papers_data = self.fetcher.fetch_daily_papers(force=force, prefer_recent=prefer_recent, max_papers=max_papers)

        # データクラスに変換
        papers = []
        for paper_data in papers_data:
            paper = ScholarPaper(
                id=paper_data["id"],
                title=paper_data["title"],
                authors=paper_data["authors"],
                year=paper_data.get("year"),
                citations=paper_data["citations"],
                link=paper_data["link"],
                pdf_link=paper_data.get("pdf_link"),
                snippet=paper_data["snippet"],
                fetched_date=paper_data["fetched_date"],
            )
            papers.append(paper)

        return papers

    def get_pdf_links(self, papers: List[ScholarPaper]) -> List[tuple[ScholarPaper, str]]:
        """
        PDFリンクが存在する論文のみを抽出

        Args:
            papers: ScholarPaperのリスト

        Returns:
            (ScholarPaper, pdf_link)のタプルのリスト
        """
        papers_with_pdf = []
        for paper in papers:
            if paper.pdf_link:
                papers_with_pdf.append((paper, paper.pdf_link))

        return papers_with_pdf

    def print_summary(self):
        """月次サマリーを表示"""
        summary = self.fetcher.get_monthly_summary()
        print("\n=== Monthly Summary ===")
        print(f"Month: {summary['month']}")
        print(f"API calls used: {summary['api_calls_used']}/100")
        print(f"Papers fetched: {summary['papers_fetched']}")
        print(f"Efficiency: {summary['efficiency']}")
        print(f"Potential papers this month: {summary['potential_papers_this_month']}")

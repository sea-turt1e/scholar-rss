import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

import requests


@dataclass
class ArxivPaper:
    """arXiv論文のデータクラス"""

    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    published: datetime
    categories: List[str]
    pdf_url: str
    arxiv_url: str


class ArxivFetcher:
    """arXiv APIから論文を取得するクラス"""

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, delay: float = 3.0):
        """
        Args:
            delay: API呼び出し間の待機時間（秒）
        """
        self.delay = delay

    def fetch_ai_papers(self, max_results: int = 10) -> List[ArxivPaper]:
        """
        AI関連の論文を取得する

        Args:
            max_results: 取得する論文の最大数

        Returns:
            ArxivPaper のリスト
        """
        # AI関連のカテゴリを検索
        search_query = "cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV OR cat:cs.NE"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()

        # XMLをパース
        root = ET.fromstring(response.content)

        papers = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)

        return papers

    def fetch_recent_papers(self, days_back: int = 1, max_results: int = 10) -> List[ArxivPaper]:
        """
        最近の論文を取得する

        Args:
            days_back: 何日前からの論文を取得するか
            max_results: 取得する論文の最大数

        Returns:
            ArxivPaper のリスト
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)

        # 日付範囲を指定した検索クエリ
        search_query = f"(cat:cs.AI OR cat:cs.LG OR cat:cs.CL OR cat:cs.CV OR cat:cs.NE) AND submittedDate:[{start_date.strftime('%Y%m%d')}* TO {end_date.strftime('%Y%m%d')}*]"

        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }

        response = requests.get(self.BASE_URL, params=params)
        response.raise_for_status()

        # XMLをパース
        root = ET.fromstring(response.content)

        papers = []
        for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
            paper = self._parse_entry(entry)
            if paper:
                papers.append(paper)

        # API制限を考慮して待機
        time.sleep(self.delay)

        return papers

    def _parse_entry(self, entry) -> Optional[ArxivPaper]:
        """
        XMLエントリからArxivPaperオブジェクトを生成

        Args:
            entry: XMLエントリ

        Returns:
            ArxivPaper オブジェクト
        """
        try:
            # タイトル
            title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
            title = title_elem.text.strip() if title_elem is not None else ""

            # 著者
            authors = []
            for author in entry.findall("{http://www.w3.org/2005/Atom}author"):
                name_elem = author.find("{http://www.w3.org/2005/Atom}name")
                if name_elem is not None:
                    authors.append(name_elem.text.strip())

            # 概要
            summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
            abstract = summary_elem.text.strip() if summary_elem is not None else ""

            # arXiv ID
            id_elem = entry.find("{http://www.w3.org/2005/Atom}id")
            if id_elem is None:
                return None
            arxiv_url = id_elem.text.strip()
            arxiv_id = arxiv_url.split("/")[-1]

            # 公開日
            published_elem = entry.find("{http://www.w3.org/2005/Atom}published")
            if published_elem is None:
                return None
            published = datetime.fromisoformat(published_elem.text.replace("Z", "+00:00"))

            # カテゴリ
            categories = []
            for category in entry.findall("{http://www.w3.org/2005/Atom}category"):
                term = category.get("term")
                if term:
                    categories.append(term)

            # PDF URL
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            return ArxivPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                arxiv_id=arxiv_id,
                published=published,
                categories=categories,
                pdf_url=pdf_url,
                arxiv_url=arxiv_url,
            )

        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None

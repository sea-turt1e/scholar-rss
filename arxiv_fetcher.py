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
    citation_count: int = 0  # 引用数を追加


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

    def fetch_recent_papers_by_citations(self, days_back: int = 1, max_results: int = 10) -> List[ArxivPaper]:
        """
        最近の論文を引用数でソートして取得する

        Args:
            days_back: 何日前からの論文を取得するか
            max_results: 取得する論文の最大数

        Returns:
            引用数でソートされたArxivPaper のリスト
        """
        # より多くの論文を取得してから引用数でソート
        papers = self.fetch_recent_papers(days_back, max_results * 3)

        # 引用数を取得（簡易版：arxiv_idからバージョンを除去して検索）
        papers_with_citations = []
        for paper in papers:
            citation_count = self._get_citation_count_simple(paper.arxiv_id)
            paper.citation_count = citation_count
            papers_with_citations.append(paper)

        # 引用数でソート（降順）
        papers_with_citations.sort(key=lambda x: x.citation_count, reverse=True)

        return papers_with_citations[:max_results]

    def fetch_ai_papers_by_citation_from_semantic_scholar(
        self, days_back: int = 7, max_results: int = 10
    ) -> List[ArxivPaper]:
        """
        Semantic ScholarからAI関連論文を被引用数順で取得し、arXiv論文のみフィルタリング

        Args:
            days_back: 何日前からの論文を取得するか
            max_results: 取得する論文の最大数

        Returns:
            被引用数でソートされたArxivPaper のリスト
        """
        try:
            # 日付範囲を計算
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Semantic Scholar API search endpoint
            url = "https://api.semanticscholar.org/graph/v1/paper/search"

            # 最小限のパラメータでテスト
            params = {
                "query": "transformer",  # 単純な1単語クエリ
                "fields": "paperId,title,authors,abstract,publicationDate,citationCount,externalIds",
                "limit": 50,  # 固定値
            }

            print(f"Semantic Scholar検索テスト中...")
            print(f"URL: {url}")
            print(f"Params: {params}")
            
            # curlコマンドを生成（手動テスト用）
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            print(f"curl '{url}?{query_string}'")

            # レート制限対応のリトライ機能
            max_retries = 3
            retry_count = 0

            while retry_count < max_retries:
                response = requests.get(url, params=params, timeout=30)

                if response.status_code == 200:
                    break
                elif response.status_code == 429:
                    # レート制限エラー
                    retry_count += 1
                    wait_time = 60 * retry_count  # 待機時間を段階的に増加
                    print(f"レート制限エラー (試行 {retry_count}/{max_retries})")
                    if retry_count < max_retries:
                        print(f"{wait_time}秒待機してリトライします...")
                        time.sleep(wait_time)
                    else:
                        print("最大リトライ回数に達しました。元のarXiv取得方式にフォールバック")
                        return self.fetch_ai_papers(max_results)
                else:
                    print(f"Semantic Scholar API error: {response.status_code}")
                    print(f"Response: {response.text}")
                    return []

            # レート制限を考慮して長めに待機
            time.sleep(5)

            data = response.json()
            papers_data = data.get("data", [])
            total = data.get("total", 0)
            print(f"Semantic Scholarから{len(papers_data)}件の論文を取得 (total: {total})")

            # arXiv論文のみフィルタリング
            arxiv_papers = []
            for paper_data in papers_data:
                external_ids = paper_data.get("externalIds", {})
                arxiv_id = external_ids.get("ArXiv")

                if arxiv_id:
                    # 最初は日付フィルタリングをスキップして、引用数の高い順にarXiv論文を取得
                    # （後で日付が合わないものもあるが、まずは取得を優先）
                    arxiv_paper = self._create_arxiv_paper_from_semantic_scholar(paper_data, arxiv_id)
                    if arxiv_paper:
                        # 日付チェック（厳密でなくても引用数の高いものを優先）
                        pub_date_str = paper_data.get("publicationDate")
                        should_include = True

                        if pub_date_str:
                            try:
                                pub_datetime = datetime.fromisoformat(pub_date_str)
                                # 日付範囲外でも、引用数が高ければ採用（緩いフィルタ）
                                if pub_datetime < start_date - timedelta(days=365):  # 1年以上古い場合のみ除外
                                    should_include = False
                            except ValueError:
                                pass  # 日付パースエラーは無視

                        if should_include:
                            arxiv_papers.append(arxiv_paper)
                            title = paper_data.get("title", "No title")[:50]
                            citation_count = paper_data.get("citationCount", 0)
                            pub_date_display = pub_date_str or "日付不明"
                            print(
                                f"  採用: {title}... (引用数: {citation_count}, 日付: {pub_date_display}, arXiv: {arxiv_id})"
                            )

                    if len(arxiv_papers) >= max_results:
                        break

            print(f"arXiv論文として{len(arxiv_papers)}件を抽出")
            return arxiv_papers

        except Exception as e:
            print(f"Semantic Scholar検索エラー: {e}")
            return []

    def _create_arxiv_paper_from_semantic_scholar(self, paper_data: dict, arxiv_id: str) -> Optional[ArxivPaper]:
        """
        Semantic ScholarのデータからArxivPaperオブジェクトを作成

        Args:
            paper_data: Semantic Scholarから取得した論文データ
            arxiv_id: arXiv ID

        Returns:
            ArxivPaper オブジェクト
        """
        try:
            title = paper_data.get("title", "")

            # 著者情報を抽出
            authors_data = paper_data.get("authors", [])
            authors = [author.get("name", "") for author in authors_data if author.get("name")]

            abstract = paper_data.get("abstract", "")
            citation_count = paper_data.get("citationCount", 0)

            # 公開日をパース
            pub_date_str = paper_data.get("publicationDate")
            if pub_date_str:
                published = datetime.fromisoformat(pub_date_str)
            else:
                published = datetime.now()

            # arXiv URLとPDF URLを生成
            arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            # カテゴリは空として設定（Semantic Scholarから取得困難）
            categories = ["cs.AI"]  # デフォルトでAI関連として設定

            return ArxivPaper(
                title=title,
                authors=authors,
                abstract=abstract,
                arxiv_id=arxiv_id,
                published=published,
                categories=categories,
                pdf_url=pdf_url,
                arxiv_url=arxiv_url,
                citation_count=citation_count,
            )

        except Exception as e:
            print(f"ArxivPaper作成エラー (ID: {arxiv_id}): {e}")
            return None

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
                citation_count=0,
            )

        except Exception as e:
            print(f"Error parsing entry: {e}")
            return None

    def _get_citation_count_simple(self, arxiv_id: str) -> int:
        """
        Semantic Scholar APIから実際の引用数を取得

        Args:
            arxiv_id: arXiv ID

        Returns:
            引用数
        """
        try:
            # arxiv_idからバージョン番号を除去
            clean_id = arxiv_id.split("v")[0]

            # Semantic Scholar Graph API v2エンドポイント
            url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{clean_id}"

            # 必要なフィールドを指定
            params = {"fields": "citationCount"}

            # デバッグ情報
            print(f"API URL: {url}")
            print(f"Parameters: {params}")

            # APIリクエスト（タイムアウト設定）
            response = requests.get(url, params=params, timeout=10)

            # レート制限を考慮して待機（100 requests per 5 minutes = 3秒間隔）
            time.sleep(3)

            # デバッグ: レスポンス詳細を出力
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response text: {response.text[:500]}...")  # 最初の500文字のみ

            if response.status_code == 200:
                data = response.json()

                # citationCountを取得
                citation_count = data.get("citationCount", 0)

                print(f"引用数取得成功: {clean_id} -> {citation_count}")
                return citation_count
            elif response.status_code == 404:
                # 論文が見つからない場合
                print(f"論文が見つかりません: {clean_id}")
                return 0
            else:
                # その他のエラー
                print(f"API error for {clean_id}: {response.status_code}")
                return 0

        except requests.exceptions.Timeout:
            print(f"API timeout for {clean_id}")
            return 0
        except requests.exceptions.RequestException as e:
            print(f"API request error for {clean_id}: {e}")
            return 0
        except Exception as e:
            print(f"Unexpected error for {clean_id}: {e}")
            return 0

import hashlib
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from serpapi import GoogleSearch

# ログ設定
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class EfficientScholarFetcher:
    """API使用を最小限に抑えた効率的な論文取得クラス（serpapi版）"""

    def __init__(self, api_key: str, cache_dir: str = "./scholar_cache"):
        """
        Args:
            api_key: SerpApiのAPIキー
            cache_dir: キャッシュと履歴を保存するディレクトリ
        """
        self.api_key = api_key
        self.cache_dir = cache_dir
        self.history_file = os.path.join(cache_dir, "fetched_papers_history.json")
        self.api_usage_file = os.path.join(cache_dir, "api_usage.json")

        # キャッシュディレクトリを作成
        os.makedirs(cache_dir, exist_ok=True)

        # 履歴とAPI使用状況を読み込み
        self.fetched_papers = self._load_history()
        self.api_usage = self._load_api_usage()

        # AI関連の効率的な検索クエリ
        # 最新論文重視の場合（初期化時に年を設定）
        current_year = datetime.now().year
        self.search_queries_recent = [
            f'"deep learning" OR "neural network" {current_year}',
            f'"transformer" OR "large language model" {current_year}',
            f'site:arxiv.org "machine learning" {current_year}',
            f'"computer vision" {current_year} filetype:pdf',
            f'"generative AI" OR "foundation model" {current_year}',
        ]

        # 高引用論文重視の場合（デフォルト）
        self.search_queries_quality = [
            '"deep learning" OR "neural network" citations:100',  # 100引用以上
            '"transformer" OR "large language model" citations:50',
            '"computer vision" OR "natural language processing" citations:100',
            '"reinforcement learning" OR "generative AI" citations:50',
            'arxiv.org "machine learning" citations:100',  # arXiv限定
        ]

        # デフォルトは高引用論文を優先
        self.search_queries = self.search_queries_quality

        # 無料論文のドメイン（主要なもののみ）
        self.free_domains = [
            "arxiv.org",
            "openreview.net",
            "aclanthology.org",
            "proceedings.neurips.cc",
            "proceedings.mlr.press",
            "openaccess.thecvf.com",
            "plos.org",
            "ncbi.nlm.nih.gov/pmc",
            "biorxiv.org",
            "medrxiv.org",
        ]

    def _load_history(self) -> Dict[str, Set[str]]:
        """取得済み論文の履歴を読み込み"""
        if os.path.exists(self.history_file):
            with open(self.history_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {date: set(papers) for date, papers in data.items()}
        return {}

    def _save_history(self):
        """取得済み論文の履歴を保存"""
        data = {date: list(papers) for date, papers in self.fetched_papers.items()}
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load_api_usage(self) -> Dict[str, int]:
        """API使用状況を読み込み"""
        if os.path.exists(self.api_usage_file):
            with open(self.api_usage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_api_usage(self):
        """API使用状況を保存"""
        with open(self.api_usage_file, "w", encoding="utf-8") as f:
            json.dump(self.api_usage, f, indent=2)

    def _get_current_month_key(self) -> str:
        """現在の月のキーを取得"""
        return datetime.now().strftime("%Y-%m")

    def _check_api_limit(self) -> tuple[bool, int]:
        """API制限をチェック"""
        month_key = self._get_current_month_key()
        current_usage = self.api_usage.get(month_key, 0)
        remaining = 100 - current_usage
        return remaining > 0, remaining

    def _increment_api_usage(self):
        """API使用回数を増やす"""
        month_key = self._get_current_month_key()
        self.api_usage[month_key] = self.api_usage.get(month_key, 0) + 1
        self._save_api_usage()

    def _get_paper_id(self, paper: Dict) -> str:
        """論文の一意なIDを生成"""
        content = f"{paper.get('title', '')}{paper.get('link', '')}"
        return hashlib.md5(content.encode()).hexdigest()

    def _is_free_paper(self, result: Dict) -> bool:
        """論文が無料でアクセス可能かどうかを判定"""
        # PDFリンクがある場合を優先チェック
        if "resources" in result:
            for resource in result.get("resources", []):
                if "link" in resource:
                    link = resource["link"].lower()
                    if link.endswith(".pdf") or any(domain in link for domain in self.free_domains):
                        return True

        # 論文リンクをチェック
        if "link" in result:
            link = result["link"].lower()
            if any(domain in link for domain in self.free_domains):
                return True

        # タイトルにarXiv識別子がある場合
        if "title" in result:
            title_lower = result["title"].lower()
            if "arxiv:" in title_lower or "[arxiv]" in title_lower:
                return True

        return False

    def _extract_citations(self, result: Dict) -> int:
        """引用数を抽出"""
        if "inline_links" in result and "cited_by" in result.get("inline_links", {}):
            cited_by = result["inline_links"]["cited_by"]
            if "total" in cited_by:
                return cited_by["total"]
        return 0

    def _extract_year(self, result: Dict) -> Optional[int]:
        """論文の年を抽出"""
        if "publication_info" in result and "summary" in result.get("publication_info", {}):
            summary = result["publication_info"]["summary"]
            import re

            year_match = re.search(r"\b(20[1-2]\d)\b", summary)
            if year_match:
                return int(year_match.group())
        return None

    def _extract_authors(self, result: Dict) -> List[str]:
        """著者情報を抽出"""
        authors = []
        if "publication_info" in result and "authors" in result.get("publication_info", {}):
            for author in result["publication_info"]["authors"]:
                if "name" in author:
                    authors.append(author["name"])
        return authors

    def _extract_pdf_link(self, result: Dict) -> Optional[str]:
        """PDFリンクを抽出（優先度付き）"""
        # PDFリソースを優先
        if "resources" in result:
            for resource in result["resources"]:
                if "link" in resource:
                    link = resource["link"]
                    if link.lower().endswith(".pdf"):
                        return link
                    # arXivなどの無料リポジトリ
                    if any(domain in link.lower() for domain in self.free_domains):
                        return link
        return None

    def _get_year_range_for_recent(self) -> tuple[int, int]:
        """最新論文検索用の年範囲を動的に計算"""
        now = datetime.now()
        current_year = now.year
        current_month = now.month

        # 年の最初の3ヶ月間は前年も含める
        if current_month <= 3:
            return (current_year - 1, current_year)
        else:
            return (current_year, current_year)

    def _update_search_queries_for_current_year(self):
        """現在の年に合わせて検索クエリを更新"""
        current_year = datetime.now().year

        # 最新論文重視のクエリを現在の年で更新
        self.search_queries_recent = [
            f'"deep learning" OR "neural network" {current_year}',
            f'"transformer" OR "large language model" {current_year}',
            f'site:arxiv.org "machine learning" {current_year}',
            f'"computer vision" {current_year} filetype:pdf',
            f'"generative AI" OR "foundation model" {current_year}',
        ]

    def fetch_daily_papers(self, force: bool = False, prefer_recent: bool = False) -> List[Dict]:
        """
        1日3件の高引用論文を取得（コスパ重視）

        Args:
            force: 今日既に取得済みでも強制的に取得するか
            prefer_recent: 最新論文を優先するか（デフォルトは高引用論文優先）

        Returns:
            取得した論文のリスト
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 既に今日の分を取得済みかチェック
        if today in self.fetched_papers and not force:
            logger.info(f"Already fetched papers for {today}")
            return []

        # API制限チェック
        can_use, remaining = self._check_api_limit()
        if not can_use:
            logger.error("Monthly API limit reached (100 calls)")
            return []

        logger.info(f"API calls remaining this month: {remaining}")

        # 検索戦略を選択
        if prefer_recent:
            # 現在の年に合わせてクエリを更新
            self._update_search_queries_for_current_year()
            queries = self.search_queries_recent
            year_range = self._get_year_range_for_recent()  # 動的に計算
            min_citations = 1  # 最新論文は引用数が少ないため
            logger.info(f"Using recent papers strategy: {year_range[0]}-{year_range[1]}")
        else:
            queries = self.search_queries_quality
            current_year = datetime.now().year
            year_range = (current_year - 2, current_year)  # 過去2年
            min_citations = 10  # 質を保証

        # 最適なクエリを選択（毎日異なるクエリを使う）
        day_of_month = datetime.now().day
        query_index = (day_of_month - 1) % len(queries)
        query = queries[query_index]

        params = {
            "engine": "google_scholar",
            "q": query,
            "api_key": self.api_key,
            "num": 20,  # 1回で20件取得
            "as_ylo": year_range[0],
            "as_yhi": year_range[1],
            "hl": "en",
        }

        # 最新論文優先の場合は日付順ソート
        if prefer_recent:
            params["scisbd"] = 0  # 日付順ソート

        logger.info(f"Searching with query: {query} (Strategy: {'recent' if prefer_recent else 'quality'})")
        try:
            # serpapi を使って検索
            search = GoogleSearch(params)
            results = search.get_dict()

            # API使用回数を記録
            self._increment_api_usage()

            if "organic_results" not in results:
                logger.warning("No organic results found")
                return []

            # 無料論文をフィルタリング
            free_papers = []
            for result in results["organic_results"]:
                if self._is_free_paper(result):
                    citations = self._extract_citations(result)

                    # 被引用数のフィルタリング
                    if citations >= min_citations:
                        paper_info = {
                            "id": self._get_paper_id(result),
                            "title": result.get("title", ""),
                            "authors": self._extract_authors(result),
                            "year": self._extract_year(result),
                            "citations": citations,
                            "link": result.get("link", ""),
                            "pdf_link": self._extract_pdf_link(result),
                            "snippet": result.get("snippet", ""),
                            "fetched_date": today,
                        }
                        free_papers.append(paper_info)

            # 被引用数で降順ソート
            free_papers.sort(key=lambda x: x["citations"], reverse=True)
            logger.info(f"Found {len(free_papers)} free papers with 10+ citations")

            # 過去に取得していない論文のみを選択
            all_fetched_ids = set()
            for date_papers in self.fetched_papers.values():
                all_fetched_ids.update(date_papers)

            new_papers = []
            for paper in free_papers:
                if paper["id"] not in all_fetched_ids:
                    new_papers.append(paper)
                    if len(new_papers) >= 3:  # 1日3件まで
                        break

            logger.info(f"Selected {len(new_papers)} new papers for today")

            # 履歴に追加
            if new_papers:
                self.fetched_papers[today] = {p["id"] for p in new_papers}
                self._save_history()

                # 結果を保存
                self._save_daily_papers(today, new_papers)

            return new_papers

        except Exception as e:
            logger.error(f"Error fetching papers: {e}")
            return []

    def _save_daily_papers(self, date: str, papers: List[Dict]):
        """その日の論文を保存"""
        filename = os.path.join(self.cache_dir, f"papers_{date}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(papers)} papers to {filename}")

    def get_monthly_summary(self) -> Dict:
        """今月の取得状況サマリー"""
        month_key = self._get_current_month_key()
        api_usage = self.api_usage.get(month_key, 0)

        # 今月取得した論文数をカウント
        papers_count = 0
        for date, papers in self.fetched_papers.items():
            if date.startswith(month_key):
                papers_count += len(papers)

        # 残り日数で取得可能な論文数を計算
        days_remaining = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - datetime.now()
        potential_papers = min(days_remaining.days * 3, (100 - api_usage) * 3)

        return {
            "month": month_key,
            "api_calls_used": api_usage,
            "api_calls_remaining": 100 - api_usage,
            "papers_fetched": papers_count,
            "efficiency": f"{papers_count / max(api_usage, 1):.2f} papers/API call",
            "potential_papers_this_month": papers_count + potential_papers,
        }

    def print_papers(self, papers: List[Dict]):
        """論文情報を見やすく表示"""
        if not papers:
            print("No new papers found today.")
            return

        print(f"\n=== Today's Top {len(papers)} AI Papers ===\n")

        for i, paper in enumerate(papers, 1):
            print(f"{i}. {paper['title']}")
            if paper["authors"]:
                authors_str = ", ".join(paper["authors"][:3])
                if len(paper["authors"]) > 3:
                    authors_str += f" ... +{len(paper['authors']) - 3} authors"
                print(f"   Authors: {authors_str}")
            print(f"   Year: {paper['year'] or 'Unknown'}")
            print(f"   Citations: {paper['citations']} 🔥")
            print(f"   Link: {paper['link']}")
            if paper["pdf_link"]:
                print(f"   PDF: {paper['pdf_link']} 📄")
            print(f"   Summary: {paper['snippet'][:150]}...")
            print()

    def get_all_fetched_papers(self, days: int = 30) -> List[Dict]:
        """過去n日間の取得済み論文を取得"""
        papers = []
        start_date = datetime.now() - timedelta(days=days)

        for date_str in sorted(self.fetched_papers.keys(), reverse=True):
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if date >= start_date:
                filename = os.path.join(self.cache_dir, f"papers_{date_str}.json")
                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as f:
                        daily_papers = json.load(f)
                        papers.extend(daily_papers)

        return papers


# 使用例
if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    # APIキーを設定
    API_KEY = os.getenv("SERP_API_KEY")

    # フェッチャーを初期化
    fetcher = EfficientScholarFetcher(API_KEY)

    # 今日の論文を取得
    # デフォルト：高引用論文優先（質重視）
    # papers = fetcher.fetch_daily_papers()

    # 最新論文を取得したい場合
    papers = fetcher.fetch_daily_papers(prefer_recent=True)

    # 結果を表示
    fetcher.print_papers(papers)

    # 月次サマリーを表示
    summary = fetcher.get_monthly_summary()
    print("\n=== Monthly Summary ===")
    print(f"Month: {summary['month']}")
    print(f"API calls used: {summary['api_calls_used']}/100")
    print(f"Papers fetched: {summary['papers_fetched']}")
    print(f"Efficiency: {summary['efficiency']}")
    print(f"Potential papers this month: {summary['potential_papers_this_month']}")

    # 過去30日間の論文一覧を取得する例
    print("\n=== Recent Papers (Last 30 days) ===")
    recent_papers = fetcher.get_all_fetched_papers(days=30)
    print(f"Total papers collected: {len(recent_papers)}")

    # cronやタスクスケジューラで毎日実行する場合の例
    # 0 9 * * * /usr/bin/python3 /path/to/your_script.py >> /path/to/logs/scholar.log 2>&1

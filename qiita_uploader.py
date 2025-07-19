import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import List, Optional

from paper_summarizer import PaperSummary


class QiitaUploader:
    """Qiita CLIを使用してQiitaの記事を自動作成するクラス"""

    def __init__(self, access_token: Optional[str] = None):
        """
        Args:
            access_token: Qiitaのアクセストークン
        """
        self.access_token = access_token or os.getenv("QIITA_ACCESS_TOKEN")
        self.qiita_cmd = "qiita"

    def create_article(self, summary: PaperSummary, private: bool = False) -> bool:
        """
        論文要約からQiitaの記事を作成する

        Args:
            summary: 論文要約データ
            private: 限定共有記事として作成するかどうか

        Returns:
            成功した場合True
        """
        try:
            # 記事のメタデータとコンテンツを作成
            article_content = self._create_article_content(summary, private)
            
            # 一時ファイルに記事を保存
            with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
                f.write(article_content)
                temp_file = f.name

            try:
                # Qiita CLIで記事を投稿
                result = subprocess.run(
                    [self.qiita_cmd, "post", temp_file],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    env={**os.environ, "QIITA_ACCESS_TOKEN": self.access_token} if self.access_token else os.environ
                )

                if result.returncode == 0:
                    print(f"✓ Article posted successfully: {result.stdout.strip()}")
                    return True
                else:
                    print(f"✗ Error posting article: {result.stderr}")
                    return False

            finally:
                # 一時ファイルを削除
                os.unlink(temp_file)

        except Exception as e:
            print(f"Error creating article for {summary.arxiv_id}: {e}")
            return False

    def create_articles(self, summaries: List[PaperSummary], private: bool = False) -> int:
        """
        複数の論文要約からQiitaの記事を作成する

        Args:
            summaries: 論文要約データのリスト
            private: 限定共有記事として作成するかどうか

        Returns:
            成功した作成数
        """
        if not self.access_token:
            print("Error: QIITA_ACCESS_TOKEN is not set")
            return 0

        success_count = 0
        
        for summary in summaries:
            print(f"Creating article for: {summary.title}")
            success = self.create_article(summary, private)
            if success:
                success_count += 1
                print(f"✓ Successfully created article for {summary.arxiv_id}")
            else:
                print(f"✗ Failed to create article for {summary.arxiv_id}")

        return success_count

    def _create_article_content(self, summary: PaperSummary, private: bool = False) -> str:
        """
        Qiita記事のコンテンツを作成する

        Args:
            summary: 論文要約データ
            private: 限定共有記事として作成するかどうか

        Returns:
            記事のMarkdownコンテンツ
        """
        # メタデータ部分
        metadata = {
            "title": f"[arXiv] {summary.title}",
            "tags": [
                {"name": "機械学習", "versions": []},
                {"name": "AI", "versions": []},
                {"name": "論文", "versions": []},
                {"name": "arXiv", "versions": []},
                {"name": "Python", "versions": []}
            ],
            "private": private,
            "updated_at": "",
            "id": None,
            "url": "",
            "likes_count": 0,
            "reactions_count": 0,
            "comments_count": 0,
            "organization_url_name": None,
            "slide": False,
            "ignorePublish": False
        }

        # コンテンツ部分
        content = f"""---
{json.dumps(metadata, ensure_ascii=False, indent=2)}
---

# {summary.title}

## 論文情報

- **著者**: {', '.join(summary.authors)}
- **arXiv ID**: [{summary.arxiv_id}]({summary.arxiv_url})
- **PDF**: [Link]({summary.pdf_url})

## 要約

{summary.summary}

## 主要なポイント

"""

        for i, point in enumerate(summary.key_points, 1):
            content += f"{i}. {point}\n"

        content += f"""
## 意義・影響

{summary.implications}

## 参考リンク

- [arXiv]({summary.arxiv_url})
- [PDF]({summary.pdf_url})

---

この記事は自動生成されました。論文の詳細については、元の論文をご確認ください。
"""

        return content

    def setup_qiita_cli(self) -> bool:
        """
        Qiita CLIのセットアップを確認する

        Returns:
            セットアップが完了している場合True
        """
        try:
            # Qiita CLIがインストールされているか確認
            result = subprocess.run([self.qiita_cmd, "--version"], capture_output=True, text=True)
            if result.returncode != 0:
                print("Error: Qiita CLI is not installed")
                print("Please install it with: npm install -g @qiita/qiita-cli")
                return False

            # アクセストークンが設定されているか確認
            if not self.access_token:
                print("Error: QIITA_ACCESS_TOKEN is not set")
                print("Please set your Qiita access token in environment variables")
                return False

            return True

        except FileNotFoundError:
            print("Error: Qiita CLI is not installed")
            print("Please install it with: npm install -g @qiita/qiita-cli")
            return False


# 使用例
def main():
    """使用例"""
    from arxiv_fetcher import ArxivFetcher
    from paper_summarizer import PaperSummarizer

    # 論文を取得
    fetcher = ArxivFetcher()
    papers = fetcher.fetch_ai_papers(max_results=1)

    # 要約を生成
    summarizer = PaperSummarizer()
    summaries = summarizer.summarize_papers(papers)

    if summaries:
        # Qiitaにアップロード
        uploader = QiitaUploader()
        if uploader.setup_qiita_cli():
            success_count = uploader.create_articles(summaries, private=True)
            print(f"Successfully created {success_count} articles")


if __name__ == "__main__":
    main()
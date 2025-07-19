import os
import re
import subprocess
from pathlib import Path
from typing import List

from paper_summarizer import PaperSummary


class QiitaUploader:
    """Qiita CLIを使用してQiitaの記事を自動作成するクラス"""

    def __init__(self, public_dir: str = "public"):
        """
        Args:
            public_dir: 記事を保存するディレクトリ
        """
        self.public_dir = Path(public_dir)

        # publicディレクトリを作成
        self.public_dir.mkdir(exist_ok=True)

        self.git_push_cmd = "./git_push_to_remote.sh"

    def create_article(self, summary: PaperSummary, private: bool = False) -> bool:
        """
        論文要約からQiitaの記事ファイルを作成する

        Args:
            summary: 論文要約データ
            private: 限定共有記事として作成するかどうか

        Returns:
            成功した場合True
        """
        try:
            # 記事のコンテンツを作成
            article_content = self._create_article_content(summary, private)

            # ファイル名を生成（安全な文字のみ使用）
            safe_title = self._create_safe_filename(summary.title)
            filename = f"{safe_title}_{summary.arxiv_id}.md"
            file_path = self.public_dir / filename

            # ファイルに保存
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(article_content)

            print(f"✓ Article file created: {file_path}")
            return True

        except Exception as e:
            print(f"Error creating article file for {summary.arxiv_id}: {e}")
            return False

    def create_articles(self, summaries: List[PaperSummary], private: bool = False) -> int:
        """
        複数の論文要約からQiitaの記事ファイルを作成する

        Args:
            summaries: 論文要約データのリスト
            private: 限定共有記事として作成するかどうか

        Returns:
            成功した作成数
        """
        success_count = 0

        for summary in summaries:
            print(f"Creating article file for: {summary.title}")
            success = self.create_article(summary, private)
            if success:
                success_count += 1
                print(f"✓ Successfully created article file for {summary.arxiv_id}")
            else:
                print(f"✗ Failed to create article file for {summary.arxiv_id}")

        return success_count

    def publish_article(self, filename: str) -> bool:
        """
        指定された記事ファイルをQiitaに投稿する

        Args:
            filename: 投稿する記事ファイル名（拡張子なし）

        Returns:
            成功した場合True
        """
        try:
            # npx qiita publish コマンドを実行
            cmd = f"{self.git_push_cmd} {filename}"
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, cwd=self.public_dir.parent)

            if result.returncode == 0:
                print(f"✓ Article '{filename}' published successfully")
                print(result.stdout)
                return True
            else:
                print(f"✗ Error publishing article '{filename}': {result.stderr}")
                return False

        except Exception as e:
            print(f"Error publishing article '{filename}': {e}")
            return False

    def publish_articles(self) -> bool:
        """
        public/フォルダ内のすべての記事をQiitaに投稿する

        Returns:
            成功した場合True
        """
        article_files = self.list_articles()
        if not article_files:
            print("No articles found to publish")
            return False

        success_count = 0
        for article_file in article_files:
            # 拡張子を除いたファイル名を取得
            filename_base = article_file.replace(".md", "")
            if self.publish_article(filename_base):
                success_count += 1

        print(f"Successfully published {success_count}/{len(article_files)} articles")
        return success_count > 0

    def _create_article_content(self, summary: PaperSummary, private: bool = False) -> str:
        """
        Qiita記事のコンテンツを作成する

        Args:
            summary: 論文要約データ
            private: 限定共有記事として作成するかどうか

        Returns:
            記事のMarkdownコンテンツ
        """
        # フロントマター部分
        content = f"""---
title: "[arXiv] {summary.title}"
tags:
  - "機械学習"
  - "AI"
  - "論文"
  - "arXiv"
  - "Python"
private: {str(private).lower()}
updated_at: ""
id: null
organization_url_name: null
slide: false
ignorePublish: false
---

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

"""

        return content

    def _create_safe_filename(self, title: str) -> str:
        """
        タイトルから安全なファイル名を生成する

        Args:
            title: 記事のタイトル

        Returns:
            安全なファイル名
        """
        # 英数字、ハイフン、アンダースコアのみ残す
        safe_title = re.sub(r"[^\w\-_\s]", "", title)
        # スペースをアンダースコアに変換
        safe_title = re.sub(r"\s+", "_", safe_title)
        # 長すぎる場合は切り詰め
        if len(safe_title) > 50:
            safe_title = safe_title[:50]
        # 末尾のアンダースコアを削除
        safe_title = safe_title.rstrip("_")

        return safe_title or "untitled"

    def push_to_github(self, filename: str) -> bool:
        """
        GitHubへpush

        Args:
            filename: プッシュするファイル名（拡張子なし）

        Returns:
            push完了したらtrue
        """
        try:
            # git pushする
            cmd = f"{self.git_push_cmd} '{filename}'.md"
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                shell=True,
                cwd=self.public_dir.parent
            )
            
            if result.returncode == 0:
                print(f"✓ Successfully pushed '{filename}' to GitHub")
                if result.stdout:
                    print(result.stdout)
                return True
            else:
                print(f"✗ Error pushing to GitHub: {result.stderr}")
                return False

        except Exception as e:
            print(f"Error executing git push command: {e}")
            return False

    def list_articles(self) -> List[str]:
        """
        public/フォルダ内の記事ファイル一覧を取得する

        Returns:
            記事ファイルのリスト
        """
        if not self.public_dir.exists():
            return []

        return [f.name for f in self.public_dir.glob("*.md")]

    def get_existing_arxiv_ids(self) -> List[str]:
        """
        既存の記事からarXiv IDを抽出する

        Returns:
            既存のarXiv IDのリスト
        """
        existing_ids = []
        article_files = self.list_articles()
        
        for filename in article_files:
            # ファイル名からarXiv IDを抽出
            # 例: "VideoITG_Multimodal_Video_Understanding_with_Instr_2507.13353v1.md"
            parts = filename.replace('.md', '').split('_')
            if len(parts) > 0:
                # 最後の部分がarXiv IDの可能性が高い
                potential_id = parts[-1]
                # arXiv IDのパターンをチェック (YYMM.NNNNN形式)
                if '.' in potential_id and len(potential_id.split('.')) == 2:
                    try:
                        year_month, paper_num = potential_id.split('.')
                        # バージョン番号がある場合は除去
                        if 'v' in paper_num:
                            paper_num = paper_num.split('v')[0]
                        # 数字かどうかチェック
                        int(year_month)
                        int(paper_num)
                        existing_ids.append(f"{year_month}.{paper_num}")
                    except ValueError:
                        continue
        
        return existing_ids

    def is_paper_already_processed(self, arxiv_id: str) -> bool:
        """
        指定されたarXiv IDの論文が既に処理済みかチェックする

        Args:
            arxiv_id: チェックするarXiv ID

        Returns:
            既に処理済みの場合True
        """
        existing_ids = self.get_existing_arxiv_ids()
        # バージョン番号を除去してチェック
        clean_id = arxiv_id.split('v')[0]
        return clean_id in existing_ids


# 使用例
# def main():
#     """使用例"""
#     from arxiv_fetcher import ArxivFetcher
#     from paper_summarizer import PaperSummarizer

#     # 論文を取得
#     fetcher = ArxivFetcher()
#     papers = fetcher.fetch_ai_papers(max_results=1)

#     # 要約を生成
#     summarizer = PaperSummarizer()
#     summaries = summarizer.summarize_papers(papers)

#     if summaries:
#         # Qiitaアップローダーを作成
#         uploader = QiitaUploader()

#         # セットアップ確認
#         if uploader.push_to_github():
#             # 記事ファイルを作成
#             success_count = uploader.create_articles(summaries, private=True)
#             print(f"Successfully created {success_count} article files")

#             # 投稿するかユーザーに確認
#             # �?Y�K����k��
#             if input("Do you want to publish these articles to Qiita? (y/n): ").lower() == 'y':
#                 uploader.publish_articles()


if __name__ == "__main__":
    main()

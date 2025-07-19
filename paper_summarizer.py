import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from arxiv_fetcher import ArxivPaper


@dataclass
class PaperSummary:
    """論文要約のデータクラス"""

    title: str
    authors: List[str]
    arxiv_id: str
    summary: str
    key_points: List[str]
    implications: str
    pdf_url: str
    arxiv_url: str


class PaperSummarizer:
    """Claude CLIを使用して論文を要約するクラス"""

    def __init__(self, enable_qiita_upload: bool = False):
        self.claude_cmd = "claude"
        self.enable_qiita_upload = enable_qiita_upload

    def summarize_paper(self, paper: ArxivPaper) -> Optional[PaperSummary]:
        """
        論文を要約する

        Args:
            paper: 要約する論文

        Returns:
            PaperSummary オブジェクト
        """
        try:
            # 要約用のプロンプトを作成
            prompt = self._create_summary_prompt(paper)

            # claude CLIを実行
            result = subprocess.run([self.claude_cmd, "-p", prompt], capture_output=True, text=True, timeout=60)

            if result.returncode != 0:
                print(f"Error running claude: {result.stderr}")
                return None

            # 要約結果をパース
            summary_text = result.stdout.strip()
            summary = self._parse_summary_result(paper, summary_text)

            return summary

        except Exception as e:
            print(f"Error summarizing paper {paper.arxiv_id}: {e}")
            return None

    def summarize_papers(self, papers: List[ArxivPaper]) -> List[PaperSummary]:
        """
        複数の論文を要約する

        Args:
            papers: 要約する論文のリスト

        Returns:
            PaperSummary のリスト
        """
        summaries = []

        for paper in papers:
            print(f"Summarizing: {paper.title}")
            summary = self.summarize_paper(paper)
            if summary:
                summaries.append(summary)

        return summaries

    def summarize_papers_with_qiita_upload(
        self,
        papers: List[ArxivPaper],
        private: bool = False,
    ) -> List[PaperSummary]:
        """
        複数の論文を要約してQiitaの記事を自動作成する

        Args:
            papers: 要約する論文のリスト
            private: 限定共有記事として作成するかどうか

        Returns:
            PaperSummary のリスト
        """
        summaries = []

        for paper in papers:
            print(f"Summarizing: {paper.title}")
            summary = self.summarize_paper(paper)
            if summary:
                summaries.append(summary)

        # Qiitaアップロードが有効な場合のみ実行
        if self.enable_qiita_upload and summaries:
            try:
                from qiita_uploader import QiitaUploader

                uploader = QiitaUploader()
                success_count = uploader.create_articles(summaries, private=private)
                print(f"Successfully created {success_count} article files")

                # GitHubに記事をプッシュ
                if summaries:
                    first_summary = summaries[0]
                    safe_title = uploader._create_safe_filename(first_summary.title)
                    filename = f"{safe_title}_{first_summary.arxiv_id}"
                    uploader.push_to_github(filename)
            except ImportError:
                print("Warning: qiita_uploader not available. Skipping Qiita upload.")
            except Exception as e:
                print(f"Error uploading to Qiita: {e}")

        return summaries

    def _create_summary_prompt(self, paper: ArxivPaper) -> str:
        """
        要約用のプロンプトを作成

        Args:
            paper: 論文データ

        Returns:
            プロンプト文字列
        """
        prompt = f"""以下のAI論文を日本語で要約してください。

タイトル: {paper.title}
著者: {', '.join(paper.authors)}
カテゴリ: {', '.join(paper.categories)}
arXiv ID: {paper.arxiv_id}

概要:
{paper.abstract}

以下の形式で要約してください：

## 要約
（3-4文で論文の概要を説明）

## 主要なポイント
1. （重要なポイント1）
2. （重要なポイント2）
3. （重要なポイント3）

## 意義・影響
（この研究の意義や今後の影響について2-3文で説明）

---

# ルール
- 回答は上記の形式に従って、技術的な内容も含めて分かりやすく日本語で説明してください。
- マークダウン形式で書いてください。
"""
        return prompt

    def _parse_summary_result(self, paper: ArxivPaper, summary_text: str) -> PaperSummary:
        """
        要約結果をパースしてPaperSummaryオブジェクトを作成

        Args:
            paper: 元の論文データ
            summary_text: 要約テキスト

        Returns:
            PaperSummary オブジェクト
        """
        # 要約テキストから各セクションを抽出
        sections = self._extract_sections(summary_text)

        # 主要なポイントを抽出
        key_points = self._extract_key_points(sections.get("主要なポイント", ""))

        return PaperSummary(
            title=paper.title,
            authors=paper.authors,
            arxiv_id=paper.arxiv_id,
            summary=sections.get("要約", summary_text),
            key_points=key_points,
            implications=sections.get("意義・影響", ""),
            pdf_url=paper.pdf_url,
            arxiv_url=paper.arxiv_url,
        )

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """
        テキストから各セクションを抽出

        Args:
            text: 要約テキスト

        Returns:
            セクション名をキーとする辞書
        """
        sections = {}
        current_section = None
        current_content = []

        for line in text.split("\n"):
            line = line.strip()

            if line.startswith("## "):
                # 前のセクションを保存
                if current_section:
                    sections[current_section] = "\n".join(current_content).strip()

                # 新しいセクションを開始
                current_section = line[3:].strip()
                current_content = []
            else:
                if current_section:
                    current_content.append(line)

        # 最後のセクションを保存
        if current_section:
            sections[current_section] = "\n".join(current_content).strip()

        return sections

    def _extract_key_points(self, key_points_text: str) -> List[str]:
        """
        主要なポイントのテキストからリストを抽出

        Args:
            key_points_text: 主要なポイントのテキスト

        Returns:
            ポイントのリスト
        """
        points = []
        for line in key_points_text.split("\n"):
            line = line.strip()
            if line and (
                line.startswith("1.") or line.startswith("2.") or line.startswith("3.") or line.startswith("-")
            ):
                # 番号や記号を除去
                point = line.split(".", 1)[-1].strip() if "." in line else line.lstrip("-").strip()
                if point:
                    points.append(point)

        return points

    def format_for_qiita(self, summary: PaperSummary) -> str:
        """
        Qiitaの記事用にフォーマット

        Args:
            summary: 論文要約

        Returns:
            Qiita用のMarkdownテキスト
        """
        formatted = f"""# {summary.title}

## 論文情報

- **著者**: {', '.join(summary.authors)}
- **arXiv ID**: [{summary.arxiv_id}]({summary.arxiv_url})
- **PDF**: [Link]({summary.pdf_url})

## 要約
{summary.summary}

## 主要なポイント
"""

        for i, point in enumerate(summary.key_points, 1):
            formatted += f"{i}. {point}\n"

        formatted += f"""
## 意義・影響
{summary.implications}

## 参考リンク

- [arXiv]({summary.arxiv_url})
- [PDF]({summary.pdf_url})

---

この記事は自動生成されました。論文の詳細については、元の論文をご確認ください。
"""
        return formatted

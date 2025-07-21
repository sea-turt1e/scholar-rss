import subprocess
from dataclasses import dataclass
from typing import Dict, List, Optional

from pdf_summarizer import OpenAIPDFSummarizer, PDFSummary
from scholar_paper_fetcher import ScholarPaper


@dataclass
class PaperSummary:
    """論文要約のデータクラス"""

    title: str
    authors: List[str]
    summary: str
    key_points: List[str]
    methodology: str
    implications: str
    pdf_url: str
    paper_link: str


class PaperSummarizer:
    """Claude CLIを使用して論文を要約するクラス"""

    def __init__(self, enable_qiita_upload: bool = False):
        self.claude_cmd = "claude"
        self.enable_qiita_upload = enable_qiita_upload
        self.openai_summarizer = OpenAIPDFSummarizer()

    def summarize_paper(self, paper: ScholarPaper) -> Optional[PaperSummary]:
        """
        論文を要約する

        Args:
            paper: 要約する論文

        Returns:
            PaperSummary オブジェクト
        """
        try:
            pdf_summary = self.openai_summarizer.summarize_paper_from_url(paper, paper.pdf_link)
            summary = self._parse_summary_result(paper, pdf_summary)
            return summary

        except Exception as e:
            print(f"Error summarizing paper {paper.id}: {e}")
            return None

    def summarize_papers(self, papers: List[ScholarPaper]) -> List[PaperSummary]:
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
        papers: List[ScholarPaper],
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
        import ipdb

        ipdb.set_trace()
        if self.enable_qiita_upload and summaries:
            try:
                from qiita_uploader import QiitaUploader

                uploader = QiitaUploader()
                success_count = uploader.create_articles(summaries, private=private)
                print(f"Successfully created {success_count} article files")

                # GitHubに記事をプッシュ
                if summaries:
                    for summary in summaries:
                        safe_title = uploader._create_safe_filename(summary.title)
                        filename = f"{safe_title}"
                        uploader.push_to_github(filename)
            except ImportError:
                print("Warning: qiita_uploader not available. Skipping Qiita upload.")
            except Exception as e:
                print(f"Error uploading to Qiita: {e}")

        return summaries

    def _create_summary_prompt(self, paper: ScholarPaper) -> str:
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
発行年: {paper.year}
論文ページ: {paper.link}
PDF Link: {paper.pdf_link}
被引用数（要約時点）: {paper.citations}

概要:
{paper.snippet}

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
- この生成での出力をそのまま要約としてアップロードします。それゆえ最初や最後にAIと判断されるような出力はしないでください。
"""
        return prompt

    def _parse_summary_result(self, paper: ScholarPaper, pdf_summary: PDFSummary) -> PaperSummary:
        """
        要約結果をパースしてPaperSummaryオブジェクトを作成

        Args:
            paper: 元の論文データ
            summary_text: 要約テキスト

        Returns:
            PaperSummary オブジェクト
        """
        # 要約テキストから各セクションを抽出
        return PaperSummary(
            title=paper.title,
            authors=paper.authors,
            summary=pdf_summary.summary,
            key_points=pdf_summary.key_points,
            methodology=pdf_summary.methodology,
            implications=pdf_summary.implications,
            pdf_url=paper.pdf_link,
            paper_link=paper.link,
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
- **論文URL**: [{summary.arxiv_id}]({summary.paper_link})
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

- [論文リンク]({summary.paper_link})
- [PDF]({summary.pdf_url})

"""
        return formatted

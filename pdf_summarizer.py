import os
import subprocess
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

import requests

try:
    from pdf2image import convert_from_path

    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    print("Warning: pdf2image not available. Please install with: pip install pdf2image")

try:
    import fitz  # PyMuPDF

    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("Warning: PyMuPDF not available. Please install with: pip install PyMuPDF")

from PyPDF2 import PdfReader, PdfWriter

from scholar_paper_fetcher import ScholarPaper


@dataclass
class PDFSummary:
    """PDF要約のデータクラス"""

    paper: ScholarPaper
    summary: str
    key_points: List[str]
    implications: str
    methodology: Optional[str] = None
    results: Optional[str] = None


class PDFSummarizer:
    """PDFを画像として処理してClaude CLIで要約するクラス"""

    def __init__(self, temp_dir: str = "./temp_pdf", output_images_dir: str = "./temp_images_for_paper"):
        """
        Args:
            temp_dir: PDFと画像の一時保存ディレクトリ
            output_images_dir: 画像を出力するディレクトリ
        """
        self.temp_dir = temp_dir
        self.output_images_dir = output_images_dir
        self.claude_cmd = "claude"
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_images_dir, exist_ok=True)

    def download_pdf(self, pdf_url: str, filename: str) -> Optional[str]:
        """
        PDFをダウンロード（改善版：セッション管理とリトライ機能付き）

        Args:
            pdf_url: PDFのURL
            filename: 保存するファイル名

        Returns:
            保存したファイルのパス
        """
        pdf_path = os.path.join(self.temp_dir, filename)

        # 複数のUser-Agentを用意
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        ]

        # セッションを使用してリトライ
        for attempt in range(len(user_agents)):
            try:
                session = requests.Session()

                # ヘッダーを設定
                headers = {
                    "User-Agent": user_agents[attempt],
                    "Accept": "application/pdf,application/octet-stream,*/*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "gzip, deflate, br",
                    "DNT": "1",
                    "Connection": "keep-alive",
                    "Upgrade-Insecure-Requests": "1",
                }

                session.headers.update(headers)

                print(f"Attempt {attempt + 1}: Downloading PDF with User-Agent {attempt + 1}")

                # PDFをダウンロード
                response = session.get(pdf_url, timeout=30, allow_redirects=True)

                if response.status_code == 200:
                    # Content-Typeをチェック
                    content_type = response.headers.get("content-type", "").lower()
                    if "pdf" in content_type or len(response.content) > 1024:  # PDFファイルまたは1KB以上のファイル
                        with open(pdf_path, "wb") as out_file:
                            out_file.write(response.content)

                        print(f"PDF downloaded successfully: {pdf_path} ({len(response.content)} bytes)")
                        return pdf_path
                    else:
                        print(f"Downloaded content is not PDF: {content_type}")
                        continue

                elif response.status_code == 403:
                    print(f"403 Forbidden with User-Agent {attempt + 1}, trying next...")
                    if attempt < len(user_agents) - 1:
                        time.sleep(2)  # 2秒待機してリトライ
                        continue
                else:
                    print(f"HTTP {response.status_code} with User-Agent {attempt + 1}")
                    if attempt < len(user_agents) - 1:
                        time.sleep(2)
                        continue

            except requests.exceptions.RequestException as e:
                print(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < len(user_agents) - 1:
                    time.sleep(2)
                    continue
            except Exception as e:
                print(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < len(user_agents) - 1:
                    time.sleep(2)
                    continue

        print(f"Failed to download PDF after {len(user_agents)} attempts")
        return None

    def extract_pages(self, pdf_path: str, max_pages: int = 50) -> Tuple[str, int]:
        """
        PDFから必要なページを抽出

        Args:
            pdf_path: PDFファイルのパス
            max_pages: 最大ページ数の閾値

        Returns:
            (抽出したPDFのパス, 総ページ数)
        """
        try:
            reader = PdfReader(pdf_path)
            total_pages = len(reader.pages)

            if total_pages <= max_pages:
                # ページ数が閾値以下の場合はそのまま使用
                return pdf_path, total_pages

            # 50ページ以上の場合は前半20ページと後半20ページを抽出
            writer = PdfWriter()

            # 前半20ページ
            for i in range(min(20, total_pages)):
                writer.add_page(reader.pages[i])

            # 後半20ページ
            start_index = max(20, total_pages - 20)
            for i in range(start_index, total_pages):
                writer.add_page(reader.pages[i])

            # 抽出したPDFを保存
            extracted_path = pdf_path.replace(".pdf", "_extracted.pdf")
            with open(extracted_path, "wb") as output_file:
                writer.write(output_file)

            print(f"Extracted {min(40, total_pages)} pages from {total_pages} total pages")
            return extracted_path, total_pages

        except Exception as e:
            print(f"Error extracting pages: {e}")
            return pdf_path, -1

    def convert_pdf_to_images(self, pdf_path: str) -> List[str]:
        """
        PDFを画像に変換（pdf2imageまたはPyMuPDFを使用）

        Args:
            pdf_path: PDFファイルのパス

        Returns:
            画像ファイルパスのリスト
        """
        # 最初にPyMuPDFを試行（依存関係が少ない）
        if PYMUPDF_AVAILABLE:
            try:
                return self._convert_with_pymupdf(pdf_path)
            except Exception as e:
                print(f"PyMuPDF conversion failed: {e}")
                print("Trying pdf2image as fallback...")

        # pdf2imageをフォールバックとして使用
        if PDF2IMAGE_AVAILABLE:
            try:
                return self._convert_with_pdf2image(pdf_path)
            except Exception as e:
                print(f"pdf2image conversion failed: {e}")
                self._print_installation_guide()
                return []

        # 両方とも利用できない場合
        print("Error: No PDF to image conversion library available")
        self._print_installation_guide()
        return []

    def _convert_with_pymupdf(self, pdf_path: str) -> List[str]:
        """
        PyMuPDFを使用してPDFを画像に変換
        """
        print("Converting PDF to images using PyMuPDF...")

        doc = fitz.open(pdf_path)
        image_paths = []
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            # 解像度を150 DPIに設定（pdf2imageと同等）
            mat = fitz.Matrix(150 / 72, 150 / 72)  # 72は標準DPI
            pix = page.get_pixmap(matrix=mat)

            image_path = os.path.join(self.output_images_dir, f"{base_name}_page_{page_num + 1}.png")
            pix.save(image_path)
            image_paths.append(image_path)

        doc.close()
        print(f"Converted {len(image_paths)} pages to images using PyMuPDF")
        return image_paths

    def _convert_with_pdf2image(self, pdf_path: str) -> List[str]:
        """
        pdf2imageを使用してPDFを画像に変換
        """
        print("Converting PDF to images using pdf2image...")

        # PDFを画像に変換
        images = convert_from_path(pdf_path, dpi=150)

        # 画像を保存
        image_paths = []
        base_name = os.path.splitext(os.path.basename(pdf_path))[0]

        for i, image in enumerate(images):
            image_path = os.path.join(self.output_images_dir, f"{base_name}_page_{i + 1}.png")
            image.save(image_path, "PNG")
            image_paths.append(image_path)

        print(f"Converted {len(image_paths)} pages to images using pdf2image")
        return image_paths

    def _print_installation_guide(self):
        """
        インストール手順を表示
        """
        print("\n=== PDF to Image Conversion Setup Guide ===")
        print("\nOption 1 (Recommended): Install PyMuPDF")
        print("  pip install PyMuPDF")
        print("  - No system dependencies required")
        print("  - Faster and more reliable")

        print("\nOption 2: Install pdf2image + poppler")
        print("  pip install pdf2image")
        print("  # Then install poppler:")
        print("  # macOS: brew install poppler")
        print("  # Ubuntu/Debian: sudo apt-get install poppler-utils")
        print("  # Windows: Download from https://blog.alivate.com.au/poppler-windows/")

        print("\nBoth libraries provide PDF to image conversion.")
        print("PyMuPDF is recommended for easier setup.\n")

    def summarize_with_claude(self, paper: ScholarPaper, image_paths: List[str]) -> Optional[PDFSummary]:
        """
        Claude CLIを使用してPDFを要約

        Args:
            paper: ScholarPaperオブジェクト
            image_paths: 画像ファイルパスのリスト

        Returns:
            PDFSummaryオブジェクト
        """
        try:
            # プロンプトを作成
            prompt = self._create_prompt(paper)

            # Claude CLIコマンドを構築
            cmd = [self.claude_cmd]

            # 画像パスを追加
            if image_paths:
                cmd.extend(["-p", "@temp_images_for_paper/"])

            # プロンプトを追加
            cmd.extend([prompt])

            # Claudeを実行
            print(f"Running Claude with {len(image_paths)} images...")

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode != 0:
                print(f"Error running Claude: {result.stderr}")
                return None

            # 結果をパース
            summary_text = result.stdout.strip()
            return self._parse_summary(paper, summary_text)

        except subprocess.TimeoutExpired:
            print("Claude timeout after 5 minutes")
            return None
        except Exception as e:
            print(f"Error summarizing with Claude: {e}")
            return None

    def convert_pdf_to_images_only(self, paper: ScholarPaper, pdf_url: str) -> List[str]:
        """
        PDFを画像に変換してtemp_images_for_paper/ディレクトリに保存

        Args:
            paper: ScholarPaperオブジェクト
            pdf_url: PDFのURL

        Returns:
            画像ファイルパスのリスト
        """
        # ファイル名を生成
        safe_title = "".join(c for c in paper.title[:50] if c.isalnum() or c in (" ", "-", "_")).rstrip()
        filename = f"{safe_title}_{paper.id}.pdf"

        # PDFをダウンロード
        pdf_path = self.download_pdf(pdf_url, filename)
        if not pdf_path:
            return []

        # ページを抽出
        extracted_path, _ = self.extract_pages(pdf_path)

        # PDFを画像に変換
        image_paths = self.convert_pdf_to_images(extracted_path)
        if not image_paths:
            print("Failed to convert PDF to images. Please check the installation guide above.")
            return []

        # 一時PDFファイルをクリーンアップ (画像ファイルは保持)
        self._cleanup_temp_files(pdf_path, extracted_path, [])

        return image_paths

    def summarize_paper_from_images(self, paper: ScholarPaper, image_paths: List[str]) -> Optional[PDFSummary]:
        """
        画像パスから論文を要約する

        Args:
            paper: ScholarPaperオブジェクト
            image_paths: 画像ファイルパスのリスト

        Returns:
            PDFSummaryオブジェクト
        """
        if not image_paths:
            print("No image paths provided")
            return None

        # Claudeで要約
        summary = self.summarize_with_claude(paper, image_paths)

        return summary

    def summarize_paper(self, paper: ScholarPaper, pdf_url: str) -> Optional[PDFSummary]:
        """
        論文を要約する完全なパイプライン

        Args:
            paper: ScholarPaperオブジェクト
            pdf_url: PDFのURL

        Returns:
            PDFSummaryオブジェクト
        """
        # ファイル名を生成
        safe_title = "".join(c for c in paper.title[:50] if c.isalnum() or c in (" ", "-", "_")).rstrip()
        filename = f"{safe_title}_{paper.id}.pdf"

        # PDFをダウンロード
        pdf_path = self.download_pdf(pdf_url, filename)
        if not pdf_path:
            return None

        # ページを抽出
        extracted_path, _ = self.extract_pages(pdf_path)

        # PDFを画像に変換
        image_paths = self.convert_pdf_to_images(extracted_path)
        if not image_paths:
            print("Failed to convert PDF to images. Please check the installation guide above.")
            return None

        # Claudeで要約
        summary = self.summarize_with_claude(paper, image_paths)

        # 一時ファイルをクリーンアップ (ただし、画像ファイルは保持)
        self._cleanup_temp_files(pdf_path, extracted_path, [])

        return summary

    def _create_prompt(self, paper: ScholarPaper) -> str:
        """要約プロンプトを作成"""
        return f"""
のフォルダに保存されている画像を使用して日本語で詳細に要約してください。
画像ファイル名の末尾にindexが書かれており、それが論文のページの順番です。

タイトル: {paper.title}
著者: {', '.join(paper.authors) if paper.authors else '不明'}
引用数: {paper.citations}
概要: {paper.snippet}

## 要約
（論文の全体的な概要を3-5文で説明）

## 主要なポイント
1. （最も重要なポイント）
2. （2番目に重要なポイント）
3. （3番目に重要なポイント）
（必要に応じて4, 5...を追加）

## 手法・アプローチ
（論文で提案された手法やアプローチを具体的に説明）

## 実験結果・成果
（主要な実験結果や成果を具体的な数値とともに説明）

## 意義・影響
（この研究の学術的・実用的な意義と今後の影響について説明）

---

# ルール
- 画像の内容を正確に読み取り、技術的な詳細も含めて説明してください
- 図表から読み取れる重要な情報も含めてください
- 専門用語は適切に日本語訳するか、カタカナ表記にしてください
- マークダウン形式で書いてください
"""

    def _parse_summary(self, paper: ScholarPaper, summary_text: str) -> PDFSummary:
        """要約結果をパース"""
        sections = {}
        current_section = None
        current_content = []

        for line in summary_text.split("\n"):
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

        # 主要なポイントを抽出
        key_points = []
        key_points_text = sections.get("主要なポイント", "")
        for line in key_points_text.split("\n"):
            line = line.strip()
            if line and (line[0].isdigit() or line.startswith("-")):
                # 番号や記号を除去
                point = line.split(".", 1)[-1].strip() if "." in line else line.lstrip("-").strip()
                if point:
                    key_points.append(point)

        return PDFSummary(
            paper=paper,
            summary=sections.get("要約", summary_text),
            key_points=key_points,
            implications=sections.get("意義・影響", ""),
            methodology=sections.get("手法・アプローチ"),
            results=sections.get("実験結果・成果"),
        )

    def cleanup_images(self, image_paths: List[str]):
        """画像ファイルをクリーンアップ"""
        try:
            for image_path in image_paths:
                if os.path.exists(image_path):
                    os.remove(image_path)
                    print(f"Deleted image: {image_path}")
        except Exception as e:
            print(f"Error cleaning up image files: {e}")

    def _cleanup_temp_files(self, pdf_path: str, extracted_path: str, image_paths: List[str]):
        """一時ファイルをクリーンアップ"""
        try:
            # PDFファイルを削除
            if os.path.exists(pdf_path):
                os.remove(pdf_path)

            # 抽出したPDFを削除（異なる場合）
            if extracted_path != pdf_path and os.path.exists(extracted_path):
                os.remove(extracted_path)

            # 画像ファイルを削除
            for image_path in image_paths:
                if os.path.exists(image_path):
                    os.remove(image_path)

        except Exception as e:
            print(f"Error cleaning up temp files: {e}")

import argparse
import os

from dotenv import load_dotenv

from pdf_summarizer import PDFSummarizer
from scholar_paper_fetcher import ScholarPaperFetcher


def main():
    parser = argparse.ArgumentParser(description="Google Scholarから論文を取得し、PDFを画像として要約")
    parser.add_argument("--force", action="store_true", help="今日既に取得済みでも強制的に取得")
    parser.add_argument("--prefer-recent", action="store_true", help="最新論文を優先（デフォルトは高引用論文）")
    parser.add_argument("--max-papers", type=int, default=3, help="要約する論文の最大数")

    args = parser.parse_args()

    # 環境変数を読み込み
    load_dotenv()

    # APIキーを取得
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        print("Error: SERP_API_KEY not found in environment variables")
        return

    # 論文を取得
    print("=== Fetching papers from Google Scholar ===")
    fetcher = ScholarPaperFetcher(api_key)
    papers = fetcher.fetch_papers(force=args.force, prefer_recent=args.prefer_recent)

    if not papers:
        print("No papers found")
        return

    # PDFリンクがある論文を抽出
    papers_with_pdf = fetcher.get_pdf_links(papers)

    if not papers_with_pdf:
        print("No papers with PDF links found")
        return

    print(f"\nFound {len(papers_with_pdf)} papers with PDF links")

    # PDFSummarizerを初期化 (temp_images_for_paperディレクトリを指定)
    summarizer = PDFSummarizer(output_images_dir="temp_images_for_paper")

    # 論文をPDF→画像変換して要約
    summaries = []
    for i, (paper, pdf_link) in enumerate(papers_with_pdf[: args.max_papers]):
        print(f"\n=== Processing paper {i + 1}/{min(len(papers_with_pdf), args.max_papers)} ===")
        print(f"Title: {paper.title}")
        print(f"Authors: {', '.join(paper.authors[:3])}...")
        print(f"Citations: {paper.citations}")
        print(f"PDF: {pdf_link}")

        # PDFを画像に変換
        image_paths = summarizer.convert_pdf_to_images_only(paper, pdf_link)

        if image_paths:
            print(f"\nPDF converted to {len(image_paths)} images in temp_images_for_paper/")

            # 画像から要約を生成
            print("Generating summary with Claude...")
            summary = summarizer.summarize_paper_from_images(paper, image_paths)

            if summary:
                summaries.append(summary)
                print("\nSummary generated successfully!")

                # 要約後に画像ファイルを削除
                print("Cleaning up image files...")
                summarizer.cleanup_images(image_paths)
            else:
                print("\nFailed to generate summary")
                # 失敗した場合も画像を削除
                summarizer.cleanup_images(image_paths)

        else:
            print("\nFailed to convert PDF to images")

    # 結果を表示
    print(f"\n\n=== Summary Results ===")
    print(f"Successfully summarized {len(summaries)} out of {min(len(papers_with_pdf), args.max_papers)} papers")

    for i, summary in enumerate(summaries, 1):
        print(f"\n{'='*60}")
        print(f"Paper {i}: {summary.paper.title}")
        print(f"{'='*60}")
        print(f"\n## 要約")
        print(summary.summary)

        print(f"\n## 主要なポイント")
        for j, point in enumerate(summary.key_points, 1):
            print(f"{j}. {point}")

        if summary.methodology:
            print(f"\n## 手法・アプローチ")
            print(summary.methodology)

        if summary.results:
            print(f"\n## 実験結果・成果")
            print(summary.results)

        print(f"\n## 意義・影響")
        print(summary.implications)

        print(f"\n論文リンク: {summary.paper.link}")
        if summary.paper.pdf_link:
            print(f"PDFリンク: {summary.paper.pdf_link}")

    # 月次サマリーを表示
    fetcher.print_summary()


if __name__ == "__main__":
    main()

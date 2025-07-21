import argparse
import os

from dotenv import load_dotenv

from paper_summarizer import PaperSummarizer
from scholar_paper_fetcher import ScholarPaperFetcher


def main():
    parser = argparse.ArgumentParser(description="Google Scholarから論文を取得し、PDFを画像として要約")
    parser.add_argument("--force", action="store_true", help="今日既に取得済みでも強制的に取得")
    parser.add_argument("--prefer-recent", action="store_true", help="最新論文を優先（デフォルトは高引用論文）")
    parser.add_argument("--max-papers", type=int, default=3, help="要約する論文の最大数")
    parser.add_argument("--qiita-upload", action="store_true", help="Qiitaの記事を自動作成する")

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

    summarizer = PaperSummarizer(enable_qiita_upload=args.qiita_upload)

    if args.qiita_upload:
        # Qiitaアップロード機能付きで実行
        summaries = summarizer.summarize_papers_with_qiita_upload(papers_with_pdf, private=args.private)
    else:
        # 通常の要約のみ
        summaries = summarizer.summarize_papers(papers)

    print(f"要約完了: {len(summaries)}")

    for summary in summaries:
        print(summary)
        print("\n")

    # 結果を表示
    for summary in summaries:
        print("\n" + "=" * 50)
        print(f"タイトル: {summary.title}")
        print(f"著者: {', '.join(summary.authors)}")
        print(f"URL: {summary.pdf_url}")
        print(f"方法: {summary.methodology}")
        print(f"要約: {summary.summary}")
        print("主要なポイント:")
        for i, point in enumerate(summary.key_points, 1):
            print(f"  {i}. {point}")
        print(f"意義・影響: {summary.implications}")


if __name__ == "__main__":
    main()

import argparse
import os

from dotenv import load_dotenv

from arxiv_fetcher import ArxivFetcher
from paper_summarizer import PaperSummarizer


def main():
    parser = argparse.ArgumentParser(description="ArXiv論文を取得・要約し、Qiitaの記事を作成")
    parser.add_argument("--max-results", type=int, default=5, help="取得する論文の最大数")
    parser.add_argument("--days-back", type=int, default=1, help="何日前からの論文を取得するか")
    parser.add_argument("--qiita-upload", action="store_true", help="Qiitaの記事を自動作成する")
    parser.add_argument("--private", action="store_true", help="限定共有記事として作成する")
    parser.add_argument("--recent", action="store_true", help="最新の論文を取得（デフォルトはAI関連論文）")

    args = parser.parse_args()

    load_dotenv()

    # 論文を取得
    fetcher = ArxivFetcher()
    if args.recent:
        papers = fetcher.fetch_recent_papers(days_back=args.days_back, max_results=args.max_results)
    else:
        papers = fetcher.fetch_ai_papers(max_results=args.max_results)

    print(f"取得した論文数: {len(papers)}")

    # 要約を生成
    summarizer = PaperSummarizer(enable_qiita_upload=args.qiita_upload)

    if args.qiita_upload:
        # Qiitaアップロード機能付きで実行
        access_token = os.getenv("QIITA_ACCESS_TOKEN")
        summaries = summarizer.summarize_papers_with_qiita_upload(
            papers, private=args.private, access_token=access_token
        )
    else:
        # 通常の要約のみ
        summaries = summarizer.summarize_papers(papers)

    print(f"要約完了: {len(summaries)}")

    # 結果を表示
    for summary in summaries:
        print("\n" + "=" * 50)
        print(f"タイトル: {summary.title}")
        print(f"著者: {', '.join(summary.authors)}")
        print(f"arXiv ID: {summary.arxiv_id}")
        print(f"要約: {summary.summary}")
        print("主要なポイント:")
        for i, point in enumerate(summary.key_points, 1):
            print(f"  {i}. {point}")
        print(f"意義・影響: {summary.implications}")


if __name__ == "__main__":
    main()

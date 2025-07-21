import argparse
import os
from datetime import datetime

from dotenv import load_dotenv

from arxiv_fetcher import ArxivFetcher
from paper_summarizer import PaperSummarizer


def main():
    parser = argparse.ArgumentParser(description="ArXiv論文を取得・要約し、Qiitaの記事を作成")
    parser.add_argument("--max-results", type=int, default=3, help="取得する論文の最大数")
    parser.add_argument("--days-back", type=int, default=7, help="何日前からの論文を取得するか")
    parser.add_argument("--qiita-upload", action="store_true", help="Qiitaの記事を自動作成する")
    parser.add_argument("--private", action="store_true", help="限定共有記事として作成する")
    parser.add_argument("--recent", action="store_true", help="最新の論文を取得（デフォルトはAI関連論文）")
    parser.add_argument("--semantic-scholar", action="store_true", help="Semantic Scholarから被引用数上位のAI関連arXiv論文を取得")

    args = parser.parse_args()

    load_dotenv()

    # 論文を取得
    fetcher = ArxivFetcher()
    
    # 取得方法を選択
    if args.semantic_scholar:
        # まずarXiv APIから論文を取得（多めに取得）
        if args.recent:
            all_papers = fetcher.fetch_recent_papers(days_back=args.days_back, max_results=args.max_results * 10)
        else:
            all_papers = fetcher.fetch_ai_papers(max_results=args.max_results * 10)
        
        # その後、Semantic Scholarで引用数を補完
        print("arXiv APIから論文を取得後、Semantic Scholarで引用数と引用速度を取得します...")
        papers_with_citations = []
        current_year = datetime.now().year
        
        for paper in all_papers:
            citation_count, citation_velocity = fetcher._get_citation_count_simple(paper.arxiv_id)
            paper.citation_count = citation_count
            paper.citation_velocity = citation_velocity
            
            # フィルタリング条件
            # 1. 引用数が0より大きい
            # 2. または、今年の論文で引用速度が0より大きい
            paper_year = paper.published.year
            if citation_count > 0 or (paper_year >= current_year and citation_velocity > 0):
                papers_with_citations.append(paper)
                print(f"取得成功: {paper.title[:50]}... (引用数: {citation_count}, 引用速度: {citation_velocity}, 年: {paper_year})")
            
            # 十分な数の論文が集まったら終了
            if len(papers_with_citations) >= args.max_results * 2:
                break
        
        # 引用数でソート（引用速度も考慮）
        papers_with_citations.sort(key=lambda x: (x.citation_count, x.citation_velocity), reverse=True)
        all_papers = papers_with_citations[:args.max_results]
        
        print(f"\n条件を満たす論文数: {len(papers_with_citations)} (要求数: {args.max_results})")
        
    elif args.qiita_upload:
        from qiita_uploader import QiitaUploader
        uploader = QiitaUploader()
        
        # より多くの論文を取得して引用数でソート
        if args.recent:
            all_papers = fetcher.fetch_recent_papers_by_citations(
                days_back=args.days_back, 
                max_results=args.max_results * 3
            )
        else:
            all_papers = fetcher.fetch_ai_papers(max_results=args.max_results * 3)
    else:
        if args.recent:
            all_papers = fetcher.fetch_recent_papers(days_back=args.days_back, max_results=args.max_results)
        else:
            all_papers = fetcher.fetch_ai_papers(max_results=args.max_results)

    # 既存ファイルのチェック用（Qiitaアップロード時のみ）
    if args.qiita_upload:
        from qiita_uploader import QiitaUploader
        uploader = QiitaUploader()
        
        # 既存ファイルをスキップ
        filtered_papers = []
        for paper in all_papers:
            if not uploader.is_paper_already_processed(paper.arxiv_id):
                filtered_papers.append(paper)
                if len(filtered_papers) >= args.max_results:
                    break
        
        papers = filtered_papers
        print(f"取得した論文数: {len(all_papers)} (既存除外後: {len(papers)})")
        
        # 引用数情報を表示
        if papers:
            print("引用数順:")
            for i, paper in enumerate(papers[:5], 1):
                print(f"  {i}. {paper.title[:50]}... (引用数: {paper.citation_count})")
    else:
        papers = all_papers
        print(f"取得した論文数: {len(papers)}")

    # 要約を生成
    summarizer = PaperSummarizer(enable_qiita_upload=args.qiita_upload)

    if args.qiita_upload:
        # Qiitaアップロード機能付きで実行
        summaries = summarizer.summarize_papers_with_qiita_upload(papers, private=args.private)
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

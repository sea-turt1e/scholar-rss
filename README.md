# Scholar RSS

arXiv APIを使用してAI関連の論文を自動取得し、Claude CLIを使って日本語で要約するPythonツールです。

## 機能

- arXiv APIからAI関連論文の自動取得
- 最新論文の取得（指定期間内）
- Claude CLIを使用した論文の日本語要約
- 構造化された要約データの生成
- Qiita記事用のMarkdownフォーマット出力
- **NEW**: Qiita CLIを使用したQiita記事の自動作成

## 必要な依存関係

- Python 3.12以上
- Claude CLI
- Qiita CLI

### パッケージ依存関係

```bash
pip install requests>=2.31.0 openai>=1.0.0 schedule>=1.2.0 python-dotenv>=1.0.0 feedparser>=6.0.0
```

または`uv`を使用：

```bash
uv install
```

## セットアップ

1. リポジトリをクローンします：
```bash
git clone <repository-url>
cd scholar-rss
```

2. 依存関係をインストールします：
```bash
uv install
```

3. Claude CLIをインストールし、設定します：
```bash
# Claude CLIのインストール方法はAnthropic公式ドキュメントを参照
claude --help
```

4. Qiita CLIをインストールし、設定します：
```bash
# Node.jsが必要
npm install -g @qiita/qiita-cli

# Qiitaのアクセストークンを環境変数に設定
export QIITA_ACCESS_TOKEN="your_qiita_access_token"
```

## 使用方法

### 基本的な使用例

```python
from arxiv_fetcher import ArxivFetcher
from paper_summarizer import PaperSummarizer

# arXiv APIから論文を取得
fetcher = ArxivFetcher(delay=3.0)
papers = fetcher.fetch_ai_papers(max_results=5)

# 論文を要約
summarizer = PaperSummarizer()
summaries = summarizer.summarize_papers(papers)

# 結果を表示
for summary in summaries:
    print(f"Title: {summary.title}")
    print(f"Summary: {summary.summary}")
    print("---")
```

### 最近の論文を取得

```python
# 過去3日間の論文を取得
recent_papers = fetcher.fetch_recent_papers(days_back=3, max_results=10)
```

### Qiita記事用にフォーマット

```python
# Qiita記事用のMarkdownを生成
for summary in summaries:
    qiita_markdown = summarizer.format_for_qiita(summary)
    print(qiita_markdown)
```

### Qiita記事自動作成

```python
from arxiv_fetcher import ArxivFetcher
from paper_summarizer import PaperSummarizer

def main():
    # 論文を取得
    fetcher = ArxivFetcher()
    papers = fetcher.fetch_ai_papers(max_results=3)
    
    # Qiitaアップロード機能を有効にして要約
    summarizer = PaperSummarizer(enable_qiita_upload=True)
    summaries = summarizer.summarize_papers_with_qiita_upload(papers, private=False)
    
    print(f"Created {len(summaries)} Qiita articles")

# 実行
main()
```

### コマンドライン使用

```bash
# 基本的な使用
python main.py

# 10件の論文を取得し、Qiita記事を自動作成
python main.py --max-results 10 --qiita-upload

# 過去3日間の論文を取得してQiita記事を作成（限定共有）
python main.py --recent --days-back 3 --qiita-upload --private

# 使用可能なオプション
python main.py --help
```

## クラス説明

### ArxivFetcher

arXiv APIから論文を取得するクラス。

**主要メソッド：**
- `fetch_ai_papers(max_results=10)`: AI関連の論文を取得
- `fetch_recent_papers(days_back=1, max_results=10)`: 最近の論文を取得

**対象カテゴリ：**
- cs.AI (Artificial Intelligence)
- cs.LG (Machine Learning)
- cs.CL (Computation and Language)
- cs.CV (Computer Vision)
- cs.NE (Neural and Evolutionary Computing)

### PaperSummarizer

Claude CLIを使用して論文を要約するクラス。

**主要メソッド：**
- `summarize_paper(paper)`: 単一論文の要約
- `summarize_papers(papers)`: 複数論文の要約
- `summarize_papers_with_qiita_upload(papers, private, access_token)`: 複数論文の要約とQiita記事自動作成
- `format_for_qiita(summary)`: Qiita記事用フォーマット

**生成される要約構造：**
- 要約（3-4文の概要）
- 主要なポイント（3つの重要点）
- 意義・影響（研究の意義と今後の影響）

### QiitaUploader

Qiita CLIを使用してQiitaの記事を自動作成するクラス。

**主要メソッド：**
- `create_article(summary, private)`: 単一論文要約から記事を作成
- `create_articles(summaries, private)`: 複数論文要約から記事を作成
- `setup_qiita_cli()`: Qiita CLIのセットアップ確認

**特徴：**
- Qiita CLIとの統合
- 公開/限定共有記事の選択
- 自動的な論文情報とタグ付け
- エラーハンドリングと進捗表示

## データクラス

### ArxivPaper

論文情報を格納するデータクラス。

```python
@dataclass
class ArxivPaper:
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    published: datetime
    categories: List[str]
    pdf_url: str
    arxiv_url: str
```

### PaperSummary

要約情報を格納するデータクラス。

```python
@dataclass
class PaperSummary:
    title: str
    authors: List[str]
    arxiv_id: str
    summary: str
    key_points: List[str]
    implications: str
    pdf_url: str
    arxiv_url: str
```

## 注意事項

- arXiv APIの利用制限に配慮し、デフォルトで3秒の待機時間が設定されています
- Claude CLIが正しくインストールされ、設定されている必要があります
- 論文の要約には時間がかかる場合があります（1論文あたり数十秒〜数分）
- Qiita記事自動作成機能を使用する場合：
  - Qiita CLIがインストールされている必要があります
  - 環境変数`QIITA_ACCESS_TOKEN`にQiitaのアクセストークンを設定する必要があります
  - アクセストークンは[Qiitaの設定ページ](https://qiita.com/settings/applications)で取得できます

## ライセンス

このプロジェクトは適切なライセンスの下で公開されています。
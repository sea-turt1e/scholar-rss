import asyncio
from typing import Optional

from playwright.async_api import async_playwright

from paper_summarizer import PaperSummary


class ZennUploader:
    """Playwrightを使用してZennスクラップを自動作成するクラス"""

    def __init__(self, headless: bool = False):
        """
        Args:
            headless: ヘッドレスモードで実行するかどうか
        """
        self.headless = headless

    async def create_scrap(self, summary: PaperSummary, login_email: Optional[str] = None) -> bool:
        """
        論文要約からZennスクラップを作成する

        Args:
            summary: 論文要約データ
            login_email: Zennログイン用メールアドレス

        Returns:
            成功した場合True
        """
        try:
            async with async_playwright() as p:
                browser = await p.firefox.launch(headless=self.headless)
                page = await browser.new_page()

                # Zennにログイン
                login_success = await self._login(page, login_email)
                if not login_success:
                    await browser.close()
                    return False

                # スクラップ作成
                success = await self._create_scrap_content(page, summary)
                await browser.close()
                return success

        except Exception as e:
            print(f"Error creating scrap for {summary.arxiv_id}: {e}")
            return False

    async def create_scraps(self, summaries: list[PaperSummary], login_email: Optional[str] = None) -> int:
        """
        複数の論文要約からZennスクラップを作成する

        Args:
            summaries: 論文要約データのリスト
            login_email: Zennログイン用メールアドレス

        Returns:
            成功した作成数
        """
        success_count = 0

        for summary in summaries:
            print(f"Creating scrap for: {summary.title}")
            success = await self.create_scrap(summary, login_email)
            if success:
                success_count += 1
                print(f"✓ Successfully created scrap for {summary.arxiv_id}")
            else:
                print(f"✗ Failed to create scrap for {summary.arxiv_id}")

            # 連続作成時の間隔を空ける
            await asyncio.sleep(2)

        return success_count

    async def _login(self, page, email: Optional[str] = None) -> bool:
        """
        Zennにログインする

        Args:
            page: Playwrightページオブジェクト
            email: ログイン用メールアドレス（使用されない）

        Returns:
            ログイン成功した場合True
        """
        try:
            # ログインページへ移動
            await page.goto("https://zenn.dev/login")
            await page.wait_for_load_state("networkidle")

            # 既にログインしている場合はスキップ
            if "/login" not in page.url:
                return True

            # Googleログインボタンを探す
            google_login_button = page.locator('a[href*="google"]')
            if await google_login_button.count() > 0:
                await google_login_button.click()
                await page.wait_for_load_state("networkidle")

            # ログイン完了を待つ（最大30秒）
            try:
                await page.wait_for_url("https://zenn.dev/dashboard", timeout=30000)
                return True
            except Exception:
                # ダッシュボードに移動しない場合は手動ログインを促す
                print("Please log in manually in the browser window...")
                try:
                    await page.wait_for_url("https://zenn.dev/dashboard", timeout=120000)
                    return True
                except Exception:
                    # ダッシュボードでなくても、ログインページから離れていればOKとする
                    if "/login" not in page.url:
                        return True
                    return False

        except Exception as e:
            print(f"Login error: {e}")
            return False

    async def _create_scrap_content(self, page, summary: PaperSummary) -> bool:
        """
        スクラップのコンテンツを作成する

        Args:
            page: Playwrightページオブジェクト
            summary: 論文要約データ

        Returns:
            作成成功した場合True
        """
        try:
            # スクラップ作成ページへ移動
            await page.goto("https://zenn.dev/scraps/new")
            await page.wait_for_load_state("networkidle")

            # タイトルを入力
            title_input = page.locator('input[name="title"]')
            await title_input.fill(f"[arXiv] {summary.title}")

            # コンテンツを作成
            content = self._format_scrap_content(summary)

            # テキストエリアに入力
            textarea = page.locator("textarea")
            await textarea.fill(content)

            # 公開設定を確認（デフォルトのままにする）

            # 作成ボタンをクリック
            submit_button = page.locator('button[type="submit"]')
            await submit_button.click()

            # 作成完了を待つ
            await page.wait_for_load_state("networkidle")

            # 成功判定（URLが変わったかどうか）
            if "/scraps/" in page.url and page.url != "https://zenn.dev/scraps/new":
                return True
            else:
                return False

        except Exception as e:
            print(f"Error creating scrap content: {e}")
            return False

    def _format_scrap_content(self, summary: PaperSummary) -> str:
        """
        スクラップ用のコンテンツを整形する

        Args:
            summary: 論文要約データ

        Returns:
            整形されたコンテンツ
        """
        content = f"""# {summary.title}

**著者**: {', '.join(summary.authors)}
**arXiv ID**: [{summary.arxiv_id}]({summary.arxiv_url})
**PDF**: [Link]({summary.pdf_url})

## 要約
{summary.summary}

## 主要なポイント
"""

        for i, point in enumerate(summary.key_points, 1):
            content += f"{i}. {point}\n"

        content += f"""
## 意義・影響
{summary.implications}

---

#AI #機械学習 #論文 #arXiv
"""
        return content


# 使用例
async def main():
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
        # Zennにアップロード
        uploader = ZennUploader(headless=False)
        success_count = await uploader.create_scraps(summaries)
        print(f"Successfully created {success_count} scraps")


if __name__ == "__main__":
    asyncio.run(main())

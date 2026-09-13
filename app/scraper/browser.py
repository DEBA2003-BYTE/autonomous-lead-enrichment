from playwright.async_api import (
    Browser,
    BrowserContext,
    Playwright,
    async_playwright,
)


class BrowserManager:

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None

    async def start(self) -> BrowserContext:

        self.playwright = await async_playwright().start()

        self.browser = await self.playwright.chromium.launch(
            headless=True,
        )

        self.context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/130.0 Safari/537.36"
            ),
            viewport={
                "width": 1440,
                "height": 900,
            },
        )

        return self.context

    async def close(self):

        if self.context:
            await self.context.close()

        if self.browser:
            await self.browser.close()

        if self.playwright:
            await self.playwright.stop()

        self.context = None
        self.browser = None
        self.playwright = None
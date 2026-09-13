from app.scraper.browser import BrowserManager


async def create_browser():

    manager = BrowserManager()

    context = await manager.start()

    return manager, context
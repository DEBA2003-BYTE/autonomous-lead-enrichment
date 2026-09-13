from app.scraper.content import (
    ContentProcessor,
)


def test_extract_email():

    page = {
        "url": "https://example.com",
        "title": "Example",
        "html": """
            <html>
                <body>
                    Contact us at
                    sales@example.com
                </body>
            </html>
        """,
        "text": "Contact us at sales@example.com",
    }

    result = ContentProcessor.process(
        page
    )

    assert (
        "sales@example.com"
        in result.emails
    )


def test_extract_linkedin():

    page = {
        "url": "https://example.com/team",
        "title": "Team",
        "html": """
            <a href="https://linkedin.com/in/johndoe">
                John Doe
            </a>
        """,
        "text": "John Doe",
    }

    result = ContentProcessor.process(
        page
    )

    assert any(
        "linkedin.com/in/johndoe"
        in url
        for url in result.linkedin_urls
    )


def test_token_count():

    page = {
        "url": "https://example.com",
        "title": "Example",
        "html": "<p>Hello world</p>",
        "text": "Hello world",
    }

    result = ContentProcessor.process(
        page
    )

    assert result.token_count > 0
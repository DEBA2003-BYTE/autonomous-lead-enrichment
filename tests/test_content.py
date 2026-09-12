from app.scraper.content import ContentProcessor


def test_email_extraction():
    processor = ContentProcessor()

    html = """
    <html>
        <body>
            <p>Contact us at hello@example.com</p>
            <p>Sales: sales@example.com</p>
        </body>
    </html>
    """

    result = processor.process(
        url="https://example.com",
        title="Example",
        html=html,
    )

    assert "hello@example.com" in result.emails
    assert "sales@example.com" in result.emails


def test_linkedin_extraction():
    processor = ContentProcessor()

    html = """
    <html>
        <body>
            <a href="https://linkedin.com/in/john-doe">
                John
            </a>
        </body>
    </html>
    """

    result = processor.process(
        url="https://example.com",
        title="Example",
        html=html,
    )

    assert len(result.linkedin_urls) == 1


def test_script_removal():
    processor = ContentProcessor()

    html = """
    <html>
        <body>
            <script>
                SECRET_JUNK_DATA
            </script>

            <h1>Company</h1>

            <p>
                We build software.
            </p>
        </body>
    </html>
    """

    result = processor.process(
        url="https://example.com",
        title="Example",
        html=html,
    )

    assert "SECRET_JUNK_DATA" not in result.text
    assert "Company" in result.text
    assert "We build software." in result.text
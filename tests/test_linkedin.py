from app.enrichment.linkedin import (
    LinkedInFinder,
)


def test_normalize_linkedin_url():

    result = (
        LinkedInFinder.normalize_linkedin_url(
            "https://www.linkedin.com/in/john-doe/"
        )
    )

    assert (
        result
        == "https://www.linkedin.com/in/john-doe"
    )


def test_invalid_linkedin_url():

    result = (
        LinkedInFinder.normalize_linkedin_url(
            "https://example.com/john"
        )
    )

    assert result is None


def test_build_query():

    query = LinkedInFinder.build_query(
        "John Doe",
        "Example",
    )

    assert '"John Doe"' in query
    assert '"Example"' in query
    assert "site:linkedin.com/in" in query
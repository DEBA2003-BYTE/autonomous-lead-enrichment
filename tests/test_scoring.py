from app.llm.schema import CompanyIntelligence, TeamMember
from app.scoring.lead_scorer import LeadScorer


def test_high_quality_lead():

    intelligence = CompanyIntelligence(
        company_overview="A software company.",
        target_audience_icp="Engineering teams and enterprises.",
        contact_emails=[
            "info@example.com",
            "sales@example.com",
            "security@example.com",
        ],
        leadership_team=[
            TeamMember(
                name="John Doe",
                role="CEO",
                linkedin_url="https://linkedin.com/in/johndoe",
            ),
            TeamMember(
                name="Jane Doe",
                role="CTO",
                linkedin_url="https://linkedin.com/in/janedoe",
            ),
            TeamMember(
                name="Alex Doe",
                role="CPO",
                linkedin_url=None,
            ),
        ],
        confidence_score=0.95,
    )

    result = LeadScorer().score(
        intelligence
    )

    assert result.score >= 75
    assert result.priority == "HIGH"


def test_low_quality_lead():

    intelligence = CompanyIntelligence(
        company_overview="A company.",
        target_audience_icp="Customers.",
        contact_emails=[],
        leadership_team=[],
        confidence_score=0.50,
    )

    result = LeadScorer().score(
        intelligence
    )

    assert result.score < 50
    assert result.priority == "LOW"


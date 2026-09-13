from typing import Dict

from app.llm.schema import CompanyIntelligence


class OutreachGenerator:
    """
    Generates deterministic outreach drafts.

    No external API call.
    """

    def generate(
        self,
        intelligence: CompanyIntelligence,
        company_domain: str,
    ) -> Dict[str, str]:

        company = company_domain

        overview = (
            intelligence.company_overview
            or "your company"
        )

        icp = (
            intelligence.target_audience_icp
            or "your team"
        )

        email = (
            "Subject: Potential opportunity for {}\n\n"
            "Hi there,\n\n"
            "I came across {} and noticed that your "
            "company works with {}.\n\n"
            "I would be interested in discussing whether "
            "our solution could help your team.\n\n"
            "Would you be open to a short conversation?\n\n"
            "Best,\n"
            "Business Development"
        ).format(
            company,
            company,
            icp,
        )

        return {
            "subject": (
                "Potential opportunity for "
                + company
            ),
            "body": email,
            "personalization_basis": overview,
        }
from typing import List, Optional

from pydantic import BaseModel, Field

from app.llm.schema import CompanyIntelligence


class LeadScore(BaseModel):
    """
    Represents the qualification score of a company.
    """

    score: int = Field(
        ge=0,
        le=100,
        description="Overall lead qualification score."
    )

    priority: str = Field(
        description="Lead priority: HIGH, MEDIUM, or LOW."
    )

    reasons: List[str] = Field(
        default_factory=list,
        description="Reasons supporting the lead score."
    )


class LeadScorer:
    """
    Rule-based lead qualification engine.

    This deliberately does not call an LLM. It uses the
    structured company intelligence already extracted.
    """

    def __init__(self):
        pass

    def score(
        self,
        intelligence: CompanyIntelligence,
    ) -> LeadScore:

        score = 0
        reasons = []

        # -----------------------------------------------------
        # 1. Company overview
        # -----------------------------------------------------

        if intelligence.company_overview:
            score += 10
            reasons.append(
                "Company has a clear business description."
            )

        # -----------------------------------------------------
        # 2. ICP quality
        # -----------------------------------------------------

        if intelligence.target_audience_icp:
            score += 15
            reasons.append(
                "A target audience / ICP was identified."
            )

        # -----------------------------------------------------
        # 3. Contact information
        # -----------------------------------------------------

        email_count = len(
            intelligence.contact_emails
        )

        if email_count >= 3:
            score += 15
            reasons.append(
                "Multiple public company contact emails were found."
            )

        elif email_count >= 1:
            score += 8
            reasons.append(
                "At least one public company email was found."
            )

        # -----------------------------------------------------
        # 4. Leadership
        # -----------------------------------------------------

        leadership_count = len(
            intelligence.leadership_team
        )

        if leadership_count >= 3:
            score += 20
            reasons.append(
                "Multiple leadership members were identified."
            )

        elif leadership_count >= 1:
            score += 10
            reasons.append(
                "At least one leadership member was identified."
            )

        # -----------------------------------------------------
        # 5. LinkedIn decision makers
        # -----------------------------------------------------

        linkedin_leaders = 0

        for member in intelligence.leadership_team:

            if member.linkedin_url:
                linkedin_leaders += 1

        if linkedin_leaders >= 2:
            score += 20
            reasons.append(
                "Multiple leadership LinkedIn profiles were found."
            )

        elif linkedin_leaders == 1:
            score += 10
            reasons.append(
                "A leadership LinkedIn profile was found."
            )

        # -----------------------------------------------------
        # 6. Confidence
        # -----------------------------------------------------

        if intelligence.confidence_score >= 0.90:
            score += 20
            reasons.append(
                "LLM extraction has high confidence."
            )

        elif intelligence.confidence_score >= 0.75:
            score += 10
            reasons.append(
                "LLM extraction has reasonable confidence."
            )

        # -----------------------------------------------------
        # Cap score
        # -----------------------------------------------------

        score = min(score, 100)

        # -----------------------------------------------------
        # Determine priority
        # -----------------------------------------------------

        if score >= 75:
            priority = "HIGH"

        elif score >= 50:
            priority = "MEDIUM"

        else:
            priority = "LOW"

        return LeadScore(
            score=score,
            priority=priority,
            reasons=reasons,
        )
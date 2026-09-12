from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TeamMember(BaseModel):
    """
    Represents a publicly identified company team member.
    """

    name: str = Field(
        min_length=1,
        description="Full name of the team member."
    )

    role: str = Field(
        min_length=1,
        description="Current role or job title."
    )

    linkedin_url: Optional[str] = Field(
        default=None,
        description=(
            "Public LinkedIn profile URL if explicitly "
            "discoverable in the provided evidence."
        )
    )

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(
        cls,
        value: Optional[str],
    ) -> Optional[str]:

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if not value.startswith(
            "https://www.linkedin.com/"
        ) and not value.startswith(
            "https://linkedin.com/"
        ):
            return None

        return value


class CompanyIntelligence(BaseModel):
    """
    Structured company intelligence extracted from
    publicly available website evidence.
    """

    company_overview: str = Field(
        min_length=1,
        description=(
            "A concise two-sentence summary explaining "
            "what the company does."
        )
    )

    target_audience_icp: str = Field(
        min_length=1,
        description=(
            "The primary ideal customer profile or target "
            "audience for the company's products or services."
        )
    )

    contact_emails: List[str] = Field(
        default_factory=list,
        description=(
            "Generic or public company email addresses "
            "explicitly found in the provided evidence. "
            "Do not invent or infer email addresses."
        )
    )

    leadership_team: List[TeamMember] = Field(
        default_factory=list,
        description=(
            "Key leadership or team members explicitly "
            "identified in the provided evidence. "
            "Do not infer people or roles."
        )
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Confidence from 0.0 to 1.0 representing how "
            "strongly the provided evidence supports the "
            "overall extracted intelligence."
        )
    )
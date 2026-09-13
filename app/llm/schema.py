from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TeamMember(BaseModel):
    """A publicly identified company team member."""

    name: str = Field(
        min_length=1,
        description="Full name of the team member.",
    )

    role: str = Field(
        min_length=1,
        description="Current role or job title.",
    )

    linkedin_url: Optional[str] = Field(
        default=None,
        description="Public LinkedIn profile URL if discovered.",
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

        if not (
            value.startswith("https://linkedin.com/")
            or value.startswith("https://www.linkedin.com/")
        ):
            return None

        return value


class CompanyIntelligence(BaseModel):
    """Structured intelligence extracted from public website evidence."""

    company_overview: str = Field(
        min_length=1,
        description="Concise description of what the company does.",
    )

    target_audience_icp: str = Field(
        min_length=1,
        description="Primary target audience or ideal customer profile.",
    )

    contact_emails: List[str] = Field(
        default_factory=list,
        description="Public company emails explicitly found in evidence.",
    )

    leadership_team: List[TeamMember] = Field(
        default_factory=list,
        description="Leadership/team members explicitly identified.",
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence in the extracted intelligence.",
    )
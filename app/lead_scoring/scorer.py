from typing import List

from app.llm.schema import CompanyIntelligence


class LeadScorer:

    def score(
        self,
        intelligence: CompanyIntelligence,
    ) -> dict:

        score = 0
        reasons: List[str] = []

        overview = (
            intelligence.company_overview
            or ""
        ).lower()

        icp = (
            intelligence.target_audience_icp
            or ""
        ).lower()

        combined_text = (
            overview + " " + icp
        )

        # -----------------------------------------------------
        # Enterprise signals
        # -----------------------------------------------------

        enterprise_keywords = [
            "enterprise",
            "large organizations",
            "large-scale",
            "global",
            "organizations",
        ]

        enterprise_matches = sum(
            1
            for keyword in enterprise_keywords
            if keyword in combined_text
        )

        if enterprise_matches >= 2:
            score += 20
            reasons.append(
                "Strong enterprise customer signal"
            )
        elif enterprise_matches == 1:
            score += 10
            reasons.append(
                "Enterprise customer signal detected"
            )

        # -----------------------------------------------------
        # Technology / engineering signals
        # -----------------------------------------------------

        technology_keywords = [
            "developer",
            "developers",
            "engineering",
            "software",
            "api",
            "platform",
            "saas",
            "cloud",
            "infrastructure",
        ]

        technology_matches = sum(
            1
            for keyword in technology_keywords
            if keyword in combined_text
        )

        if technology_matches >= 5:
            score += 20
            reasons.append(
                "Strong technology and engineering profile"
            )
        elif technology_matches >= 3:
            score += 12
            reasons.append(
                "Technology-focused customer profile"
            )
        elif technology_matches >= 1:
            score += 5

        # -----------------------------------------------------
        # Security / compliance signals
        # -----------------------------------------------------

        security_keywords = [
            "security",
            "compliance",
            "governance",
            "regulated",
            "soc 2",
            "hipaa",
            "pci",
            "access control",
        ]

        security_matches = sum(
            1
            for keyword in security_keywords
            if keyword in combined_text
        )

        if security_matches >= 3:
            score += 20
            reasons.append(
                "Strong security or compliance requirements"
            )
        elif security_matches >= 1:
            score += 10
            reasons.append(
                "Security or compliance signal detected"
            )

        # -----------------------------------------------------
        # Contactability
        # -----------------------------------------------------

        email_count = len(
            intelligence.contact_emails
        )

        linkedin_count = sum(
            1
            for member in intelligence.leadership_team
            if member.linkedin_url
        )

        if email_count >= 3:
            score += 10
            reasons.append(
                "Multiple public contact emails discovered"
            )
        elif email_count >= 1:
            score += 5
            reasons.append(
                "Public company contact email discovered"
            )

        if linkedin_count >= 2:
            score += 10
            reasons.append(
                "Multiple leadership LinkedIn profiles discovered"
            )
        elif linkedin_count == 1:
            score += 5
            reasons.append(
                "Leadership LinkedIn profile discovered"
            )

        # -----------------------------------------------------
        # Leadership discovery
        # -----------------------------------------------------

        leadership_count = len(
            intelligence.leadership_team
        )

        if leadership_count >= 3:
            score += 10
            reasons.append(
                "Multiple leadership members identified"
            )
        elif leadership_count >= 1:
            score += 5
            reasons.append(
                "Company leadership identified"
            )

        # -----------------------------------------------------
        # Confidence adjustment
        # -----------------------------------------------------

        if intelligence.confidence_score >= 0.9:
            score += 5
            reasons.append(
                "High-confidence company intelligence"
            )
        elif intelligence.confidence_score >= 0.75:
            score += 3

        # -----------------------------------------------------
        # Cap score
        # -----------------------------------------------------

        score = min(score, 100)

        # -----------------------------------------------------
        # Qualification
        # -----------------------------------------------------

        if score >= 80:
            qualification = "HIGH"
            priority = "A"

        elif score >= 60:
            qualification = "MEDIUM"
            priority = "B"

        elif score >= 40:
            qualification = "LOW"
            priority = "C"

        else:
            qualification = "POOR"
            priority = "D"

        return {
            "lead_score": score,
            "qualification": qualification,
            "priority": priority,
            "reasons": reasons,
        }
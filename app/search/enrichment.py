from typing import Any, Dict, Optional

from app.enrichment.linkedin import LinkedInFinder


class LeadershipEnricher:

    def __init__(
        self,
        finder: Optional[LinkedInFinder] = None,
    ):

        self.finder = finder

    async def enrich(
        self,
        domain: str,
        intelligence: Dict[str, Any],
    ) -> Dict[str, Any]:

        intelligence = intelligence or {}

        leadership = intelligence.get(
            "leadership_team",
            [],
        )

        if not leadership:
            return intelligence

        if self.finder is None:
            return intelligence

        enriched = []

        for member in leadership:

            member_copy = dict(member)

            if member_copy.get(
                "linkedin_url"
            ):
                enriched.append(member_copy)
                continue

            name = member_copy.get(
                "name"
            )

            if not name:
                enriched.append(member_copy)
                continue

            linkedin_url = await self.finder.search_profile(
                name=name,
                company=domain,
            )

            if linkedin_url:
                member_copy[
                    "linkedin_url"
                ] = linkedin_url

            enriched.append(member_copy)

        intelligence[
            "leadership_team"
        ] = enriched

        return intelligence
from typing import Any, Dict, List, Optional


class CompanyResult:

    def __init__(
        self,
        domain: str,
    ):

        self.domain = domain
        self.success = False
        self.error: Optional[str] = None

        self.pages: List[Dict[str, Any]] = []

        self.intelligence: Optional[
            Dict[str, Any]
        ] = None

        self.score: Optional[
            Dict[str, Any]
        ] = None

        self.outreach: Optional[
            Dict[str, Any]
        ] = None

        self.cost: Optional[
            Dict[str, Any]
        ] = None

    def to_dict(self) -> Dict[str, Any]:

        return {
            "domain": self.domain,
            "success": self.success,
            "error": self.error,
            "pages": self.pages,
            "intelligence": self.intelligence,
            "score": self.score,
            "outreach": self.outreach,
            "cost": self.cost,
        }
import os
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.llm.prompts import (
    OUTREACH_SYSTEM_PROMPT,
    build_outreach_prompt,
)


class OutreachGenerator:
    """
    Generates personalized outreach using an LLM.

    The generator receives:
        - company intelligence
        - lead scoring
        - company domain

    and produces structured outreach content.

    The LLM is intentionally used here because
    personalized outreach is one of the core agent
    capabilities of the system.
    """

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set."
            )

        self.client = AsyncOpenAI(
            api_key=api_key
        )

        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-4o-mini",
            )
        )

    async def generate(
        self,
        domain: str,
        intelligence: Dict[str, Any],
        lead_scoring: Dict[str, Any],
    ) -> Dict[str, Any]:

        intelligence = intelligence or {}
        lead_scoring = lead_scoring or {}

        if not domain:
            raise ValueError(
                "Company domain is required."
            )

        prompt = build_outreach_prompt(
            domain=domain,
            intelligence=intelligence,
            lead_scoring=lead_scoring,
        )

        response = await self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": OUTREACH_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        )

        output = response.output_text.strip()

        if not output:
            raise ValueError(
                "LLM returned empty outreach content."
            )

        return self._parse_response(
            output=output,
            lead_scoring=lead_scoring,
        )

    @staticmethod
    def _parse_response(
        output: str,
        lead_scoring: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert the LLM's simple structured text into
        a predictable dictionary.

        Expected format:

        SUBJECT: ...
        GREETING: ...
        BODY:
        ...
        """

        lines = output.splitlines()

        subject = ""
        greeting = ""
        body_lines = []

        mode = None

        for line in lines:

            stripped = line.strip()

            if stripped.startswith("SUBJECT:"):
                subject = stripped[
                    len("SUBJECT:"):
                ].strip()

            elif stripped.startswith("GREETING:"):
                greeting = stripped[
                    len("GREETING:"):
                ].strip()

            elif stripped == "BODY:":
                mode = "body"

            elif mode == "body":
                body_lines.append(line)

        body = "\n".join(
            body_lines
        ).strip()

        # -------------------------------------------------
        # Fallbacks
        # -------------------------------------------------

        if not subject:
            subject = "Potential opportunity"

        if not greeting:
            greeting = "Hi there,"

        if not body:
            body = output

        score = lead_scoring.get(
            "score",
            0,
        )

        priority = lead_scoring.get(
            "priority",
            "C",
        )

        return {
            "subject": subject,
            "greeting": greeting,
            "body": body,
            "priority": str(priority),
            "lead_score": str(score),
        }
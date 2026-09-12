import os
from typing import Optional

from openai import AsyncOpenAI

from app.llm.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.llm.schema import CompanyIntelligence


class LLMExtractor:

    def __init__(
        self,
        model: Optional[str] = None,
    ):
        # -----------------------------------------------------
        # Load API key
        # -----------------------------------------------------

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set."
            )

        # -----------------------------------------------------
        # Initialize OpenAI client
        # -----------------------------------------------------

        self.client = AsyncOpenAI(
            api_key=api_key
        )

        # -----------------------------------------------------
        # Model configuration
        # -----------------------------------------------------

        self.model = (
            model
            or os.getenv(
                "OPENAI_MODEL",
                "gpt-5.6-luna",
            )
        )

        # -----------------------------------------------------
        # Basic configuration
        # -----------------------------------------------------

        self.max_evidence_chars = int(
            os.getenv(
                "MAX_EVIDENCE_CHARS",
                "100000",
            )
        )

    async def extract(
        self,
        company_domain: str,
        evidence: str,
    ) -> CompanyIntelligence:

        # -----------------------------------------------------
        # Validate domain
        # -----------------------------------------------------

        if not company_domain.strip():
            raise ValueError(
                "Company domain cannot be empty."
            )

        # -----------------------------------------------------
        # Validate evidence
        # -----------------------------------------------------

        if not evidence.strip():
            raise ValueError(
                "Cannot extract intelligence from empty evidence."
            )

        # -----------------------------------------------------
        # Prevent accidentally huge prompts
        # -----------------------------------------------------

        if len(evidence) > self.max_evidence_chars:
            evidence = evidence[
                :self.max_evidence_chars
            ]

        # -----------------------------------------------------
        # Build prompts
        # -----------------------------------------------------

        user_prompt = build_user_prompt(
            company_domain,
            evidence,
        )

        # -----------------------------------------------------
        # Call OpenAI structured output API
        # -----------------------------------------------------

        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            text_format=CompanyIntelligence,
        )

        # -----------------------------------------------------
        # Validate structured output
        # -----------------------------------------------------

        if response.output_parsed is None:
            raise ValueError(
                "LLM returned no structured output."
            )

        return response.output_parsed
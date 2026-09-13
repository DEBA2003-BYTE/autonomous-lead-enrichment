import os
from typing import Any, Dict, Optional

from openai import AsyncOpenAI

from app.llm.prompts import (
    SYSTEM_PROMPT,
    build_user_prompt,
)
from app.llm.schema import CompanyIntelligence


class LLMExtractor:
    """
    Extract structured company intelligence using OpenAI.

    Token usage is recorded for cost tracking.
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
                "gpt-5.6-luna",
            )
        )

        self.last_usage: Dict[str, Any] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

    async def extract(
        self,
        company_domain: str,
        evidence: str,
    ) -> CompanyIntelligence:

        if not evidence or not evidence.strip():
            raise ValueError(
                "Cannot extract intelligence from empty evidence."
            )

        response = await self.client.responses.parse(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": build_user_prompt(
                        company_domain,
                        evidence,
                    ),
                },
            ],
            text_format=CompanyIntelligence,
            max_output_tokens=2000,
        )

        usage = getattr(
            response,
            "usage",
            None,
        )

        if usage:

            input_tokens = getattr(
                usage,
                "input_tokens",
                0,
            ) or 0

            output_tokens = getattr(
                usage,
                "output_tokens",
                0,
            ) or 0

            total_tokens = getattr(
                usage,
                "total_tokens",
                input_tokens + output_tokens,
            ) or 0

            self.last_usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
            }

        else:

            self.last_usage = {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
            }

        parsed = getattr(
            response,
            "output_parsed",
            None,
        )

        if parsed is None:
            raise ValueError(
                "LLM returned no structured output."
            )

        return parsed

    def get_usage(self) -> Dict[str, Any]:
        return dict(self.last_usage)
import os
from typing import Any, Dict


class CostTracker:

    def __init__(self):

        self.input_price_per_million = float(
            os.getenv(
                "OPENAI_INPUT_PRICE_PER_MILLION",
                "0",
            )
        )

        self.output_price_per_million = float(
            os.getenv(
                "OPENAI_OUTPUT_PRICE_PER_MILLION",
                "0",
            )
        )

    def calculate(
        self,
        usage: Dict[str, Any],
    ) -> Dict[str, Any]:

        usage = usage or {}

        input_tokens = int(
            usage.get(
                "input_tokens",
                0,
            )
        )

        output_tokens = int(
            usage.get(
                "output_tokens",
                0,
            )
        )

        total_tokens = int(
            usage.get(
                "total_tokens",
                input_tokens + output_tokens,
            )
        )

        input_cost = (
            input_tokens
            / 1_000_000
            * self.input_price_per_million
        )

        output_cost = (
            output_tokens
            / 1_000_000
            * self.output_price_per_million
        )

        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "estimated_input_cost_usd": round(
                input_cost,
                8,
            ),
            "estimated_output_cost_usd": round(
                output_cost,
                8,
            ),
            "estimated_cost_usd": round(
                input_cost + output_cost,
                8,
            ),
        }
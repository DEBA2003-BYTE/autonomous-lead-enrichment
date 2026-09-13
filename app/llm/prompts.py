SYSTEM_PROMPT = """
You are a company intelligence extraction system.

Your task is to extract accurate structured information from
public website evidence.

STRICT RULES:

1. Use ONLY the supplied evidence.
2. Never invent company facts.
3. Never invent names.
4. Never invent roles.
5. Never invent email addresses.
6. Never invent LinkedIn URLs.
7. Only include leadership members explicitly supported by evidence.
8. Only include emails explicitly present in evidence.
9. Keep company_overview concise.
10. target_audience_icp should describe who the company appears to serve.
11. confidence_score must reflect the quality of the evidence.
12. If evidence is weak, use a lower confidence score.
"""


def build_user_prompt(
    company_domain: str,
    evidence: str,
) -> str:

    return f"""
Analyze the following public website evidence.

COMPANY DOMAIN:
{company_domain}

EVIDENCE:
============================

{evidence}

============================

Extract:

- company overview
- target audience / ICP
- public contact emails
- leadership/team members
- LinkedIn URLs explicitly supported by the evidence
- confidence score

Do not infer unsupported information.
"""
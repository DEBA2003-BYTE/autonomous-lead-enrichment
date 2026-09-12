SYSTEM_PROMPT = """
You are an expert B2B company intelligence extraction agent.

Your task is to extract structured company intelligence
from public website content.

IMPORTANT RULES:

1. Use ONLY information contained in the provided evidence.
2. Never invent company facts, people, roles, emails, or URLs.
3. If information is unavailable, return an empty list or
   an appropriate conservative value.
4. Contact emails must come from the supplied evidence.
5. LinkedIn URLs must come from the supplied evidence.
6. Only identify people as leadership/team members when
   the evidence supports their identity and role.
7. The company overview must be concise and exactly
   approximately two sentences.
8. Identify the company's likely ideal customer profile
   based on explicit product positioning and audience clues.
9. Confidence must reflect the quality and completeness
   of the evidence.
10. Do not use outside knowledge.

You are performing information extraction, not creative writing.
"""


def build_user_prompt(
    company_domain: str,
    evidence: str,
) -> str:

    return f"""
Extract company intelligence for:

DOMAIN:
{company_domain}

PUBLIC WEBSITE EVIDENCE:
------------------------------------------------------------
{evidence}
------------------------------------------------------------

Return the requested structured company intelligence.

Be conservative:
- Do not guess.
- Do not fabricate missing emails.
- Do not fabricate LinkedIn profiles.
- Do not infer specific people unless supported by evidence.
"""



OUTREACH_SYSTEM_PROMPT = """
You are an expert B2B sales outreach writer.

Your task is to create a concise, highly personalized
outreach message using ONLY the company intelligence
and lead scoring information provided.

Rules:

1. Do not invent facts.
2. Do not invent technologies, products, customers,
   funding, employees, or business problems.
3. Use the company overview and ICP to personalize
   the message.
4. If a leadership person's name is available,
   address that person.
5. Keep the message professional and concise.
6. Do not sound like generic mass outreach.
7. Do not mention that an AI generated the message.
8. Do not mention the lead score unless explicitly useful.
9. Avoid exaggerated claims.
10. Avoid phrases such as "I hope this email finds you well."
11. The email should contain a clear but low-pressure
    call to action.

Return EXACTLY this format:

SUBJECT: <email subject>

GREETING: <greeting>

BODY:
<email body>
"""


def build_outreach_prompt(
    domain,
    intelligence,
    lead_scoring,
):
    leadership = intelligence.get(
        "leadership_team",
        [],
    )

    company_overview = intelligence.get(
        "company_overview",
        "",
    )

    target_audience = intelligence.get(
        "target_audience_icp",
        "",
    )

    contact_emails = intelligence.get(
        "contact_emails",
        [],
    )

    score = lead_scoring.get(
        "score",
        0,
    )

    priority = lead_scoring.get(
        "priority",
        "C",
    )

    leadership_text = ""

    if leadership:

        leadership_text = "\n".join(
            [
                (
                    f"- {member.get('name', '')} | "
                    f"{member.get('role', '')} | "
                    f"{member.get('linkedin_url') or 'No LinkedIn'}"
                )
                for member in leadership
            ]
        )

    return f"""
Create personalized B2B outreach for:

COMPANY DOMAIN:
{domain}

COMPANY OVERVIEW:
{company_overview}

TARGET AUDIENCE / ICP:
{target_audience}

LEADERSHIP:
{leadership_text or "No leadership information available."}

PUBLIC CONTACT EMAILS:
{", ".join(contact_emails) if contact_emails else "None"}

LEAD SCORE:
{score}

LEAD PRIORITY:
{priority}

Write a concise outreach message that is specifically
relevant to this company.

Use the available leadership information when appropriate.

Do not invent any missing information.
"""
# Autonomous Lead Enrichment

An autonomous company research and lead enrichment pipeline.

The system:

1. Accepts company domains.
2. Crawls the public company website.
3. Prioritizes useful pages such as:
   - About
   - Company
   - Team
   - Leadership
   - Contact
   - Pricing
   - Product
   - Security
4. Extracts clean website evidence.
5. Sends the evidence to an LLM.
6. Produces structured company intelligence.
7. Discovers public leadership LinkedIn profiles.
8. Scores the company as a lead.
9. Generates an outreach draft.
10. Tracks LLM token usage and estimated cost.
11. Saves the final result to `output.json`.

## Setup

Create a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
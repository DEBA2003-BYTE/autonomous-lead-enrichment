# Autonomous Lead Enrichment System

**An end-to-end AI-powered lead intelligence pipeline** that autonomously researches company websites, extracts structured business intelligence, discovers leadership teams, enriches LinkedIn profiles, scores lead quality, generates personalized outreach messaging, and tracks LLM usage with cost estimation.

---

## 🚀 Quick Start (2 minutes)

### Prerequisites
- **Python 3.9+**
- **OpenAI API key** (required)
- **SerpAPI key** (optional, for search enrichment)
- **Tavily API key** (optional, for web search)

### 1️⃣ Clone & Install

```bash
# Clone the repository
git clone <repository-url>
cd autonomous-lead-enrichment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2️⃣ Configure Environment Variables

```bash
# Copy the example .env file
cp .env.example .env

# Edit .env and add your API keys:
# OPENAI_API_KEY=sk-...your-key-here...
# OPENAI_MODEL=gpt-4o
# OPENAI_INPUT_PRICE_PER_MILLION=3.00
# OPENAI_OUTPUT_PRICE_PER_MILLION=6.00
```

**Required in `.env`:**
```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o
OPENAI_INPUT_PRICE_PER_MILLION=3.00
OPENAI_OUTPUT_PRICE_PER_MILLION=6.00
```

**Optional:**
```env
SERPAPI_KEY=your_serpapi_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### 3️⃣ Run the Pipeline

**Process a single domain:**
```bash
python run.py example.com
```

**Process multiple domains:**
```bash
python run.py example.com competitor.com startup.io
```

**Output:**
Results are saved to `output.json` with:
- ✅ Company intelligence (overview, ICP, team, emails)
- ✅ Leadership information with LinkedIn URLs
- ✅ Lead quality score (0-100)
- ✅ Personalized outreach messaging
- ✅ Cost breakdown (input/output tokens + USD)

### Example Output Structure

```json
{
  "domains": [
    {
      "domain": "example.com",
      "success": true,
      "processed_at": "2024-01-15T10:30:00Z",
      "intelligence": {
        "company_overview": "Example is a leading B2B SaaS platform...",
        "target_audience_icp": "Mid-market tech companies...",
        "contact_emails": ["hello@example.com"],
        "leadership_team": [
          {
            "name": "John Doe",
            "role": "CEO",
            "linkedin_url": "https://www.linkedin.com/in/johndoe"
          }
        ],
        "confidence_score": 0.92
      },
      "lead_score": {
        "score": 85,
        "reasoning": "Strong fit based on team size and market positioning"
      },
      "outreach": {
        "subject": "Scaling to example.com - Let's talk",
        "body": "Hi Example team, I noticed you're in the SaaS space..."
      },
      "cost": {
        "input_tokens": 1250,
        "output_tokens": 340,
        "total_tokens": 1590,
        "estimated_cost_usd": 0.00579
      }
    }
  ]
}
```

---

## 🎯 What This System Does

This system transforms a company domain into a comprehensive, actionable sales intelligence record. Given a domain (e.g., `example.com`), it:

1. **🕷️ Crawls the website** using headless browser automation (Playwright) with intelligent page discovery
2. **🧹 Processes & cleans content** using BeautifulSoup with metadata preservation
3. **📊 Builds evidence packages** with token-aware prioritization of the most relevant pages
4. **🤖 Extracts structured intelligence** via LLM using Pydantic schemas with validation
5. **👥 Identifies leadership** and discovers LinkedIn profiles through search enrichment
6. **📈 Calculates lead scores** using a deterministic, rule-based qualification engine
7. **✉️ Generates outreach** with personalized messaging templates
8. **💰 Tracks costs** with real-time token usage and estimated API expenditure
9. **💾 Outputs structured JSON** with comprehensive results

## 📋 Pipeline Overview

```
Input: company.com
           │
           ▼
    ┌─────────────────────┐
    │  Website Crawler    │
    │ • HomePage Fetch    │
    │ • Link Discovery    │
    │ • Multi-page Crawl  │
    │ • 30s Timeout/Page  │
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────────┐
    │ Content Processing      │
    │ • HTML → Text          │
    │ • Metadata Extraction  │
    │ • Cleaning & Parsing   │
    └──────────┬──────────────┘
               │
               ▼
    ┌─────────────────────────────┐
    │ Evidence Builder            │
    │ • Page Ranking              │
    │ • Token Budgeting (8K limit)│
    │ • High-Signal Content       │
    └──────────┬──────────────────┘
               │
               ▼
    ┌──────────────────────────────┐
    │ LLM Extraction (OpenAI)       │
    │ • Structured Pydantic Output │
    │ • Schema Validation          │
    │ • Token Tracking             │
    └────────┬─────────────┬────────┘
             │             │
             ▼             ▼
        ┌─────────┐   ┌──────────────┐
        │ Company │   │ Leadership   │
        │ Details │   │ + Team Info  │
        └─────────┘   └──────┬───────┘
                             │
                             ▼
                    ┌────────────────────┐
                    │ LinkedIn Enrichment │
                    │ Search & Fetch URLs│
                    └─────────┬──────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
       ┌─────────┐    ┌──────────┐    ┌──────────────┐
       │  Score  │    │ Outreach │    │ Cost Metrics │
       │ Ranking │    │  Message │    │ Token Track  │
       └─────────┘    └──────────┘    └──────────────┘
            │              │                  │
            └──────────────┼──────────────────┘
                           │
                           ▼
                    ┌─────────────────┐
                    │  output.json    │
                    │ (Structured Result)
                    └─────────────────┘
```

## 🏗️ Architecture & Components

### 1. **Scraper Module** (`app/scraper/`)
**Efficient DOM handling with Playwright headless browser integration**

- **`browser.py`**: `BrowserManager` class
  - Launches chromium in headless mode
  - Manages browser context with realistic user agent
  - Handles async lifecycle (start/close)
  - Reusable context for multiple pages

- **`crawler.py`**: `WebsiteCrawler` class
  - Intelligent link discovery with keyword scoring (about, team, leadership, pricing, etc.)
  - Excludes non-relevant pages (blog, docs, login, status, etc.)
  - Fetches homepage and discovers up to 8 internal pages
  - Per-page 30-second timeout with error recovery
  - HTTP status code validation (handles 4xx/5xx gracefully)
  - Normalizes URLs and hostnames consistently

- **`content.py`**: `ContentProcessor` class
  - Cleans HTML to plain text using BeautifulSoup
  - Preserves metadata (title, description, URL, status code)
  - Removes scripts, styles, and redundant whitespace
  - Extracts structured metadata for relevance ranking

### 2. **LLM Module** (`app/llm/`)
**Reliable Pydantic schemas with prompt robustness and token filtering**

- **`schema.py`**: Pydantic models for structured output
  - `TeamMember`: name, role, linkedin_url (with validation)
  - `CompanyIntelligence`: company_overview, target_audience_icp, contact_emails, leadership_team, confidence_score (0-1)
  - Strict field validation: min lengths, URL format checks, type enforcement
  - No raw HTML dumps—only extracted intelligence

- **`prompts.py`**: System and user prompts
  - Engineering-focused prompt design for reliability
  - Asks LLM to extract facts from evidence only
  - Specifies confidence scoring logic
  - Prevents hallucination with ground-truth emphasis

- **`extractor.py`**: `LLMExtractor` class
  - Async OpenAI client with structured output via `responses.parse()`
  - Validates evidence is non-empty before API call
  - Tracks input/output tokens for cost calculation
  - Max output tokens limited to 2000 to prevent bloat
  - Raises errors on missing API key or empty evidence

- **`evidence.py`**: `build_evidence()` function
  - Token budgeting: prioritizes pages up to 8K tokens
  - Uses tiktoken for accurate token counting
  - Ranks pages by relevance (title keywords, description, content)
  - Ensures highest-signal content is included
  - Gracefully degrades if no pages are relevant

### 3. **Models Module** (`app/models/`)
**Company data structures with type hints**

- **`company.py`**: `CompanyResult` class
  - Holds domain, success flag, error messages
  - Aggregates pages, intelligence, score, outreach, cost
  - Serializable to dict for JSON output
  - Type-annotated fields for clarity

### 4. **Scoring Module** (`app/scoring/`)
**Deterministic lead qualification engine**

- **`scorer.py`**: `LeadScorer` class
  - Rule-based scoring (not ML) for reproducibility
  - Factors: confidence score, team size, company stage signals, ICP match
  - Returns 0-100 numeric score with reasoning
  - Handles missing data gracefully (defaults to neutral scoring)

### 5. **Outreach Module** (`app/outreach/`)
**Personalized message generation**

- **`generator.py`**: `OutreachGenerator` class
  - Generates templates personalized with company name, ICP, key contacts
  - Separates subject line and body message
  - Includes call-to-action with clear value proposition
  - Adaptive messaging based on company type

### 6. **Metrics Module** (`app/metrics/`)
**Cost tracking and token usage**

- **`cost.py`**: `CostTracker` class
  - Accumulates input/output tokens across all LLM calls
  - Multiplies tokens by configurable per-million pricing
  - Calculates estimated USD cost in real-time
  - Supports different pricing tiers for input vs. output

### 7. **Search Module** (`app/search/`)
**LinkedIn and search enrichment**

- **`linkedin.py`**: LinkedIn profile discovery
  - Searches for team members by name
  - Attempts to fetch public LinkedIn URLs
  - Handles network errors with retry logic (via tenacity)
  - Enriches `TeamMember` objects with LinkedIn URLs

- **`enrichment.py`**: General enrichment utilities
  - Extends company data with external sources
  - Centralized API for 3rd-party integrations

### 8. **Utils Module** (`app/utils/`)
**Logging and utilities**

- **`logger.py`**: Structured logging
  - Setup logger with consistent formatting
  - Tracks progress through pipeline stages
  
- **`cost.py`**: Cost utilities
  - Formatting and display helpers for cost data

## 🛡️ Error Handling & Resilience

This system is built for production reliability:

### Network & Timeout Handling
- **Per-page timeouts (30s)**: Prevents hanging on slow/unresponsive sites
- **Retry logic (tenacity)**: Automatic retries for transient failures
- **HTTP error handling**: Gracefully handles 4xx/5xx responses, marks as error but continues
- **Anti-bot detection**: Realistic user agents, viewport sizes, and request headers

### Data Validation
- **Pydantic validation**: All LLM output is validated against schemas before use
- **Field constraints**: LinkedIn URLs must match pattern, confidence scores are 0-1, names have min length
- **Empty field handling**: Missing data doesn't crash pipeline—defaults to empty lists or None values
- **Confidence scoring**: Extracted intelligence includes confidence metric to flag low-quality extractions

### Rate Limiting & Cost Control
- **Token budgeting**: Evidence is capped at 8K tokens—prevents runaway LLM costs
- **Cost tracking**: Real-time monitoring of token usage and USD estimates
- **API key validation**: Checks for OPENAI_API_KEY at startup before processing

### Evidence Quality
- **Non-empty validation**: Refuses to call LLM with empty evidence (prevents wasteful API calls)
- **Relevance filtering**: Pages ranked by keyword matching (about, team, leadership prioritized)
- **Page filtering**: Excludes non-business pages (blog, docs, login) automatically

##  Example Output

See `output.json` in the repository for a complete example of the pipeline output for a real company domain.

## 🧪 Testing

Run the test suite:
```bash
pytest tests/ -v
```

### Current Tests
- **`test_content.py`**: Content processing and HTML cleaning
- **`test_linkedin.py`**: LinkedIn profile discovery and enrichment
- **`test_scoring.py`**: Lead scoring with various input scenarios

### Test Coverage
- ✅ URL normalization
- ✅ Content extraction and cleaning
- ✅ Schema validation
- ✅ Error handling for missing fields
- ✅ Token counting and budgeting
- ✅ Lead scoring logic

## 🔑 Key Features

### 1. **Intelligent Web Crawling**
- Discovers most relevant pages automatically
- Avoids bloat (no blog archives, docs, status pages)
- Handles pagination and internal links
- Respects site structure and crawl boundaries

### 2. **Smart Evidence Building**
- Token-aware prioritization (fits within LLM context window)
- Keyword ranking for business-relevant content
- Deduplication and quality filtering
- Graceful degradation when content is limited

### 3. **Structured Extraction**
- Pydantic schemas for type safety and validation
- LLM output is always validated before use
- Confidence scoring for transparency
- No raw HTML in output (only extracted facts)

### 4. **Cost Transparency**
- Real-time token tracking per domain
- Accurate USD cost estimation
- Supports custom pricing tiers
- Helps forecast budget before scaling

### 5. **Resilient & Production-Ready**
- Timeouts on every operation (30s per page)
- Graceful error handling and logging
- Type hints throughout codebase
- Comprehensive schema validation

## 📁 Project Structure

```
autonomous-lead-enrichment/
├── app/
│   ├── scraper/          # Web crawling & content extraction
│   │   ├── browser.py    # Playwright headless browser
│   │   ├── crawler.py    # Link discovery & page fetching
│   │   └── content.py    # HTML → text processing
│   ├── llm/              # LLM integration & extraction
│   │   ├── extractor.py  # OpenAI async client
│   │   ├── evidence.py   # Token-aware evidence building
│   │   ├── prompts.py    # System & user prompts
│   │   └── schema.py     # Pydantic models
│   ├── models/           # Data models
│   │   └── company.py    # CompanyResult class
│   ├── scoring/          # Lead qualification
│   │   └── scorer.py     # Rule-based scoring engine
│   ├── outreach/         # Message generation
│   │   └── generator.py  # Personalized templates
│   ├── search/           # Profile enrichment
│   │   ├── linkedin.py   # LinkedIn discovery
│   │   └── enrichment.py # General enrichment
│   ├── metrics/          # Cost tracking
│   │   └── cost.py       # Token & USD tracking
│   └── utils/            # Utilities
│       ├── logger.py     # Structured logging
│       └── cost.py       # Cost formatting
├── tests/                # Unit & integration tests
├── run.py                # Main entry point
├── requirements.txt      # Python dependencies
├── .env.example          # API key template
├── output.json           # Sample output
└── README.md            # This file
```

## 🔌 API Keys Required

| Service | Purpose | Environment Variable | Required |
|---------|---------|----------------------|----------|
| OpenAI | LLM extraction & analysis | `OPENAI_API_KEY` | ✅ Yes |
| OpenAI | Model pricing | `OPENAI_INPUT_PRICE_PER_MILLION`, `OPENAI_OUTPUT_PRICE_PER_MILLION` | ✅ Yes |
| SerpAPI | Web search (optional) | `SERPAPI_KEY` | ⭕ Optional |
| Tavily | Web search (optional) | `TAVILY_API_KEY` | ⭕ Optional |

## 📈 Performance & Scalability

### Single Domain Processing
- **Average time**: 2-4 minutes per domain
- **Network calls**: 8-12 page fetches
- **LLM calls**: 1 structured extraction call
- **Typical cost**: $0.01-0.05 per domain (depending on site complexity)

### Batch Processing
- Process multiple domains sequentially with aggregated costs
- Reusable browser context reduces startup overhead
- Token budgeting prevents runaway costs on verbose sites

### Resource Requirements
- **Memory**: ~200MB (browser + Python runtime)
- **CPU**: Minimal (I/O bound, mostly network waits)
- **Network**: ~2-5 MB per domain (page downloads)

## 🐛 Troubleshooting

### Common Issues

**"OPENAI_API_KEY is not set"**
- Ensure `.env` file exists with `OPENAI_API_KEY` value
- Verify you've run `python run.py` from the project root

**"Failed to fetch homepage"**
- Site may be blocking automated requests
- Check if domain is correct (e.g., `example.com` not `example.com/page`)
- Try increasing timeout or checking firewall rules

**"No relevant pages discovered"**
- Site structure may not match expected patterns
- Check robots.txt permissions
- Manually inspect the `output.json` to see which pages were found

**"LLM extraction returned low confidence"**
- Website may not contain enough business information
- Try a competitor's domain to verify system works
- Check that evidence isn't being filtered too aggressively

## 📜 Code Quality

### Type Hints
All functions and classes use type hints for clarity:
```python
async def extract(
    self,
    company_domain: str,
    evidence: str,
) -> CompanyIntelligence:
```

### Separation of Concerns
- **Scraper**: Fetching and cleaning
- **LLM**: Intelligence extraction
- **Scoring**: Lead qualification
- **Outreach**: Message generation
- **Metrics**: Cost tracking

No module depends on implementation details of others—pure dependency injection.

### Error Handling
Every operation that can fail has explicit error handling:
```python
if not evidence or not evidence.strip():
    raise ValueError("Cannot extract intelligence from empty evidence.")
```


**Built with:**
- 🤖 **Playwright** - Headless browser automation
- 🧠 **OpenAI** - Structured LLM extraction
- 📦 **Pydantic** - Schema validation
- 🔄 **AsyncIO** - Async/await concurrency
- ✅ **Pytest** - Testing framework

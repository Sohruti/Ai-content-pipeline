# Founder Intelligence Pipeline

Automatically learns how the founder writes by analyzing LinkedIn posts and generating a knowledge base for the Platform Writer.

## How It Works

```
Fetch LinkedIn Posts
    ↓
Check for Duplicates
    ↓
Store Raw JSON
    ↓
Clean Posts
    ↓
Analyze Writing Patterns
    ↓
Generate Processed Knowledge Files
    ↓
Generate Master Knowledge File (founder_posts.md)
    ↓
Update FAISS Embeddings
    ↓
Founder Brain uses knowledge base
```

## Quick Start

```bash
# Install Apify client (optional, for live fetching)
pip install httpx

# Run the pipeline
python founder_ingestion.py
```

## Configuration

Add to your `.env`:

```env
# Founder Configuration
FOUNDER_NAME=Udit Agrawal
FOUNDER_LINKEDIN_URL=https://www.linkedin.com/in/udit003/

# LinkedIn Fetching Method
# "local" - uses data/founder_posts/raw/linkedin_posts.json
# "apify" - fetches live from LinkedIn via Apify
LINKEDIN_FETCH_METHOD=local

# Apify (optional, for live fetching)
APIFY_API_KEY=your_apify_api_key_here
```

## Fetching Methods

### Local (Default)
Store posts manually in `data/founder_posts/raw/linkedin_posts.json`:

```json
{
  "posts": [
    {
      "text": "Your post content here...",
      "date": "2026-01-15",
      "engagement": {"likes": 50, "comments": 10},
      "url": "https://linkedin.com/posts/...",
      "platform": "linkedin"
    }
  ]
}
```

### Apify (Recommended for Production)
1. Create an account at https://apify.com
2. Get your API key
3. Set `LINKEDIN_FETCH_METHOD=apify` in `.env`
4. Add `APIFY_API_KEY=your_key` to `.env`

## What Gets Generated

### Processed Files (`data/founder_posts/processed/`)
- `writing_style.md` - Sentence length, tone, formality
- `hooks.md` - Detected hook patterns
- `storytelling.md` - Narrative structures used
- `vocabulary.md` - Power words and phrases
- `opinions.md` - Founder's expressed beliefs
- `communication.md` - Communication approach
- `brand_voice.md` - Overall brand voice
- `cta_patterns.md` - Call-to-action patterns
- `product_positioning.md` - How products are positioned

### Master File (`data/founder_posts/founder_posts.md`)
Combined knowledge file used by Founder Brain. Contains:
- Writing style summary
- Hook patterns
- Storytelling structure
- Vocabulary
- Business philosophy
- Product positioning
- Communication rules
- CTA style
- Writing do's and don'ts
- Recent sample posts

## Architecture

```
app/services/
├── founder_fetcher.py      # Interface + LinkedIn provider
├── post_cleaner.py         # Removes noise from posts
├── founder_analyzer.py     # Extracts writing patterns
└── founder_ingestion.py    # Orchestrates the pipeline

data/founder_posts/
├── raw/                    # Raw JSON posts
│   └── linkedin_posts.json
├── processed/              # Individual knowledge files
│   ├── writing_style.md
│   ├── hooks.md
│   └── ...
└── founder_posts.md        # Master knowledge file
```

## Adding New Platforms

To add support for X, Medium, or Blogs:

1. Create a new fetcher in `founder_fetcher.py`:

```python
class XFetcher(FounderFetcher):
    def fetch(self, limit: int = 20) -> FetchedPosts:
        # Implement X API fetching
        ...

    def get_platform(self) -> str:
        return "x"
```

2. Register in `get_fetcher()`:

```python
fetchers = {
    "linkedin": LinkedInFetcher,
    "x": XFetcher,  # Add here
}
```

3. Run: `python founder_ingestion.py --platform x`

## Refreshing Knowledge

Run the pipeline periodically to keep the knowledge base current:

```bash
# Weekly refresh
python founder_ingestion.py

# Force re-analysis
python founder_ingestion.py --force

# Fetch more posts
python founder_ingestion.py --limit 50
```

## How Founder Brain Uses This

1. Founder Brain searches `founder_posts.md` using FAISS
2. Retrieves relevant sections based on the content topic
3. Passes writing style, hooks, vocabulary, and opinions to Platform Writer
4. Platform Writer generates content that sounds like the founder

**Important:** The system learns writing *patterns*, not content.
It never copies posts - it applies the founder's style to new topics.

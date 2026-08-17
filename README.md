# 2OS GTM Content Operating System

An AI-powered content pipeline that helps the founder of Second Order Systems (2OS) consistently create business-first LinkedIn content.

## What Is This?

This is NOT a chatbot. This is NOT a blog generator.

This is a **GTM Content Operating System** that:

1. Studies company knowledge
2. Researches external news and trends
3. Decides what content to create
4. Generates founder-quality LinkedIn content
5. Reviews and approves the content
6. Produces the final output

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run the pipeline
python main.py

# Or with a custom topic
python main.py "AI Governance in Healthcare"
```

## Architecture

```
Knowledge → Research → Strategy → Founder Brain → Story Architect → Platform Writer → Review
```

Each stage is an isolated agent with a single responsibility, connected via a LangGraph workflow.

## Project Structure

```
linkedin-ai-os/
├── main.py                    # Entry point
├── app/
│   ├── agents/               # 7 specialized agents
│   ├── services/             # LLM, VectorStore, Embeddings, etc.
│   ├── graphs/               # LangGraph pipeline
│   ├── models/               # Pydantic state models
│   └── config/               # Configuration
├── prompts/                  # Prompt templates
├── data/                     # Knowledge sources
├── outputs/                  # Generated content
└── tests/                    # Test suite
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM inference |
| `GROQ_MODEL` | LLM model (default: llama-3.3-70b-versatile) |
| `TAVILY_API_KEY` | Tavily API key for web research |
| `EMBEDDING_MODEL` | Sentence transformer model |

## License

Proprietary - Second Order Systems

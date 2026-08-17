# Tools & Dependencies

## Core Framework
| Tool | Purpose | Version |
|------|---------|---------|
| Python | Runtime | 3.11+ |
| LangGraph | Pipeline orchestration | 0.2+ |
| LangChain | LLM integration | 0.3+ |
| Pydantic | Data validation | 2.0+ |

## AI/ML
| Tool | Purpose | Version |
|------|---------|---------|
| Groq API | LLM inference | - |
| Tavily API | Web search | 0.5+ |
| Sentence Transformers | Embeddings | 3.0+ |
| FAISS | Vector search | 1.8+ |

## Utilities
| Tool | Purpose | Version |
|------|---------|---------|
| python-dotenv | Environment vars | 1.0+ |
| Rich | Terminal formatting | 13.0+ |
| NumPy | Numerical operations | 1.26+ |

## API Keys Required

### Groq API
- Used for: LLM inference (llama-3.3-70b-versatile)
- Get key: https://console.groq.com
- Cost: Pay-per-use

### Tavily API
- Used for: Web research and news
- Get key: https://tavily.com
- Cost: Free tier available

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Unix
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

## Development Tools
- pytest for testing
- ruff for linting
- mypy for type checking

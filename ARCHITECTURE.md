# Architecture

## System Overview

The 2OS GTM Content Operating System is built as a pipeline of specialized AI agents, orchestrated by LangGraph.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Pipeline                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │Knowledge │───▶│ Research │───▶│ Strategy │                  │
│  │  Agent   │    │  Agent   │    │  Agent   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│                                      │                          │
│                                      ▼                          │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                  │
│  │ Platform │◀───│  Story   │◀───│ Founder  │                  │
│  │  Writer  │    │ Architect│    │  Brain   │                  │
│  └──────────┘    └──────────┘    └──────────┘                  │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────┐                                                 │
│  │  Review  │──▶ (rewrite loop or finalize)                   │
│  │  Agent   │                                                 │
│  └──────────┘                                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Agents (Single Responsibility)
| Agent | Responsibility |
|-------|---------------|
| Knowledge Agent | Reads and synthesizes company data |
| Research Agent | Gathers external context via Tavily |
| Strategy Agent | Decides content strategy (GTM perspective) |
| Founder Brain | Retrieves founder style via vector search |
| Story Architect | Creates story blueprint |
| Platform Writer | Generates LinkedIn post |
| Review Agent | Scores and approves content |

### Services (Shared Infrastructure)
| Service | Purpose |
|---------|---------|
| LLM | Groq API wrapper for LLM inference |
| VectorStore | FAISS-based semantic search |
| Embeddings | Sentence Transformers for vectorization |
| PromptLoader | Loads prompt templates from disk |
| Logger | Structured logging with Rich |

### Data Flow
1. **Input**: Topic string
2. **Knowledge**: Company context loaded from markdown files
3. **Research**: External context from Tavily search
4. **Strategy**: Content strategy (angle, audience, messaging)
5. **Founder Brain**: Relevant founder context from vector search
6. **Story**: Story blueprint (hook, problem, insight, lesson, CTA)
7. **Draft**: LinkedIn post generated
8. **Review**: Scored against quality criteria
9. **Output**: Final approved content saved to disk

## Technology Stack
- **Orchestration**: LangGraph
- **LLM**: Groq (llama-3.3-70b-versatile)
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Vector Store**: FAISS
- **Search**: Tavily
- **Models**: Pydantic v2
- **Language**: Python 3.11+

## Design Principles
1. **Single Responsibility**: Each agent does one thing well
2. **Loose Coupling**: Agents communicate via state, not direct calls
3. **Extensibility**: New agents can be added without changing existing ones
4. **Observable**: Comprehensive logging at every stage
5. **Fail-Safe**: Max iteration limits, graceful error handling

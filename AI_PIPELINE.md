# AI Pipeline

## Pipeline Flow

```
Topic Input
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 1: Knowledge Agent                     │
│ - Reads company markdown files               │
│ - Synthesizes knowledge context              │
│ - Output: KnowledgeContext                   │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 2: Research Agent                      │
│ - Tavily web search                          │
│ - Analyzes industry trends                   │
│ - Competitor insights                        │
│ - Output: ResearchSummary                    │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 3: Strategy Agent                      │
│ - Determines business angle                  │
│ - Identifies target persona                  │
│ - Defines messaging & goals                  │
│ - Output: ContentStrategy                    │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 4: Founder Brain                       │
│ - Vector search for founder context          │
│ - Retrieves relevant stories/opinions        │
│ - Output: Founder context string             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 5: Story Architect                     │
│ - Creates hook, problem, insight             │
│ - Structures business lesson                │
│ - Output: StoryBlueprint                     │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 6: Platform Writer                     │
│ - Generates LinkedIn post                    │
│ - Matches founder voice                      │
│ - Output: Draft string                       │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ Stage 7: Review Agent                        │
│ - Scores: Voice, Business, Readability       │
│ - Scores: Authenticity, CXO Relevance        │
│ - Decision: Approve (≥9) or Rewrite (<9)     │
│ - Output: ReviewScore                        │
└─────────────────────────────────────────────┘
    │
    ├─── Score < 9 ──▶ Rewrite Loop (max 3 iterations)
    │
    └─── Score ≥ 9 ──▶ Final Output
```

## State Model

The pipeline state flows through all stages:

```python
PipelineState:
    topic: str                    # Input topic
    knowledge: KnowledgeContext   # From Knowledge Agent
    research: ResearchSummary     # From Research Agent
    strategy: ContentStrategy     # From Strategy Agent
    founder_context: str          # From Founder Brain
    story: StoryBlueprint         # From Story Architect
    draft: str                    # From Platform Writer
    review: ReviewScore           # From Review Agent
    final_output: str             # Final approved content
    iteration: int                # Current review iteration
```

## Review Loop

```
Platform Writer → Review → [Score ≥ 9] → Final Output
                    │
                    └── [Score < 9] → Platform Writer (with feedback)
```

- Maximum 3 iterations before forced approval
- Review feedback is passed to Platform Writer for rewriting
- Each iteration is tracked and logged

## Quality Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Founder Voice | 25% | Matches Udit's authentic tone |
| Business-First | 25% | Leads with outcomes, not features |
| Readability | 20% | Clear, engaging, well-structured |
| Authenticity | 15% | Genuine, not salesy |
| CXO Relevance | 15% | Resonates with target buyers |

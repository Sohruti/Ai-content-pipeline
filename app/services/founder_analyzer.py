"""Founder Analyzer - extracts reusable writing intelligence from posts.

This service does NOT summarize or copy posts.
It extracts patterns, styles, and thinking that the Platform Writer can use.
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.config.settings import (
    FOUNDER_NAME,
    FOUNDER_POSTS_DIR,
    FOUNDER_PROCESSED_DIR,
    FOUNDER_MASTER_FILE,
)
from app.models.founder import (
    FounderIntelligence,
    FounderOpinion,
    HookPattern,
    WritingStyle,
)
from app.models.state import PipelineState
from app.services.llm import invoke_llm
from app.services.logger import get_logger
from app.services.prompt_loader import load_prompt

logger = get_logger(__name__)


def _extract_writing_stats(posts: list[str]) -> dict:
    """Extract statistical writing patterns from posts.

    Args:
        posts: List of cleaned post texts.

    Returns:
        Dictionary with writing statistics.
    """
    all_sentences = []
    all_words = []
    word_counter = Counter()
    paragraph_lengths = []

    for post in posts:
        # Split into paragraphs (double newline)
        paragraphs = [p.strip() for p in post.split("\n\n") if p.strip()]
        paragraph_lengths.append(len(paragraphs))

        for paragraph in paragraphs:
            # Split into sentences (simple split on . ! ?)
            sentences = [s.strip() for s in paragraph.replace("!", ".").replace("?", ".").split(".") if s.strip()]
            all_sentences.extend(sentences)

            for sentence in sentences:
                words = sentence.split()
                all_words.extend(words)
                for word in words:
                    clean_word = word.lower().strip(".,!?;:\"'()-")
                    if len(clean_word) > 2:
                        word_counter[clean_word] += 1

    avg_sentence_length = len(all_words) / max(len(all_sentences), 1)
    avg_paragraph_length = sum(paragraph_lengths) / max(len(paragraph_lengths), 1)
    most_common_words = [word for word, _ in word_counter.most_common(50)]

    return {
        "avg_sentence_length": int(avg_sentence_length),
        "avg_paragraph_length": int(avg_paragraph_length),
        "total_words": len(all_words),
        "total_sentences": len(all_sentences),
        "most_common_words": most_common_words,
    }


def _detect_patterns(posts: list[str]) -> dict:
    """Detect hook patterns, CTA patterns, and storytelling structure.

    Args:
        posts: List of cleaned post texts.

    Returns:
        Dictionary with detected patterns.
    """
    hooks = []
    cta_patterns = []
    storytelling_patterns = []

    for post in posts:
        lines = [l.strip() for l in post.split("\n") if l.strip()]
        if not lines:
            continue

        # Extract hook (first line)
        first_line = lines[0]
        hooks.append(first_line)

        # Extract potential CTA (last meaningful line)
        for line in reversed(lines):
            if any(keyword in line.lower() for keyword in ["what", "how", "share", "comment", "think", "curious", "agree"]):
                cta_patterns.append(line)
                break

        # Detect storytelling patterns
        if any(marker in post.lower() for marker in ["here's what", "the truth is", "most people", "i learned", "we discovered"]):
            storytelling_patterns.append("insight_sharing")

        if any(marker in post.lower() for marker in ["when i", "i remember", "back in", "years ago", "i was"]):
            storytelling_patterns.append("personal_anecdote")

        if any(marker in post.lower() for marker in ["→", "1.", "first", "step 1", "here's how"]):
            storytelling_patterns.append("structured_list")

    # Count hook patterns
    hook_counter = Counter(hooks)
    top_hooks = [{"pattern": h, "count": c} for h, c in hook_counter.most_common(10)]

    return {
        "hooks": top_hooks,
        "cta_patterns": list(set(cta_patterns))[:10],
        "storytelling_patterns": list(set(storytelling_patterns)),
    }


def _analyze_with_llm(posts: list[str]) -> dict:
    """Use LLM to extract deeper intelligence from posts.

    Args:
        posts: List of cleaned post texts.

    Returns:
        Dictionary with LLM-extracted intelligence.
    """
    # Combine posts for analysis (limit to avoid token issues)
    combined = "\n\n---\n\n".join(posts[:20])

    system_prompt = """You are an expert writing analyst. Analyze the founder's posts and extract reusable intelligence.

DO NOT summarize the posts.
DO NOT copy content.
DO extract patterns, styles, and thinking.

Return a JSON object with these fields:
{
    "tone": ["list of detected tones"],
    "business_themes": ["list of business themes discussed"],
    "industries": ["industries mentioned or implied"],
    "business_philosophy": ["key beliefs and principles expressed"],
    "opinions": [{"topic": "...", "stance": "..."}],
    "product_positioning": ["how the product/company is positioned"],
    "communication_style": "description of communication approach",
    "writing_dos": ["things the founder does well"],
    "writing_donts": ["things the founder avoids"],
    "vocabulary": ["power words and phrases frequently used"]
}"""

    user_prompt = f"""Analyze these posts by {FOUNDER_NAME}:

{combined}

Extract the intelligence as JSON."""

    try:
        response = invoke_llm(system_prompt, user_prompt)

        # Parse JSON from response
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")

    return {}


def analyze_posts(posts: list[str]) -> FounderIntelligence:
    """Perform complete analysis of founder posts.

    Args:
        posts: List of cleaned post texts.

    Returns:
        FounderIntelligence with all extracted patterns.
    """
    logger.info(f"Analyzing {len(posts)} posts for founder intelligence")

    # Extract statistical patterns
    stats = _extract_writing_stats(posts)

    # Detect structural patterns
    patterns = _detect_patterns(posts)

    # Get LLM-powered analysis
    llm_analysis = _analyze_with_llm(posts)

    # Build intelligence object
    intelligence = FounderIntelligence(
        writing_style=WritingStyle(
            avg_sentence_length=stats["avg_sentence_length"],
            avg_paragraph_length=stats["avg_paragraph_length"],
            tone=llm_analysis.get("tone", []),
            formality="conversational",
            uses_short_sentences=stats["avg_sentence_length"] < 20,
            uses_line_breaks=True,
            uses_emojis=False,
            uses_hashtags=False,
        ),
        hook_patterns=[
            HookPattern(pattern=h["pattern"], frequency=h["count"])
            for h in patterns.get("hooks", [])
        ],
        vocabulary=llm_analysis.get("vocabulary", stats["most_common_words"][:20]),
        business_themes=llm_analysis.get("business_themes", []),
        industries=llm_analysis.get("industries", []),
        storytelling_pattern=", ".join(patterns.get("storytelling_patterns", [])),
        cta_patterns=patterns.get("cta_patterns", []),
        business_philosophy=llm_analysis.get("business_philosophy", []),
        opinions=[
            FounderOpinion(topic=o["topic"], stance=o["stance"])
            for o in llm_analysis.get("opinions", [])
        ],
        product_positioning=llm_analysis.get("product_positioning", []),
        communication_style=llm_analysis.get("communication_style", ""),
        writing_dos=llm_analysis.get("writing_dos", []),
        writing_donts=llm_analysis.get("writing_donts", []),
        posts_analyzed=len(posts),
        last_updated=datetime.now().isoformat(),
    )

    logger.info(f"Analysis complete: {len(intelligence.hook_patterns)} hooks, {len(intelligence.opinions)} opinions")
    return intelligence


def generate_processed_files(intelligence: FounderIntelligence) -> None:
    """Generate individual knowledge files in processed/ directory.

    Args:
        intelligence: The analyzed founder intelligence.
    """
    FOUNDER_PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    files = {
        "writing_style.md": _format_writing_style,
        "hooks.md": _format_hooks,
        "storytelling.md": _format_storytelling,
        "vocabulary.md": _format_vocabulary,
        "opinions.md": _format_opinions,
        "communication.md": _format_communication,
        "brand_voice.md": _format_brand_voice,
        "cta_patterns.md": _format_cta_patterns,
        "product_positioning.md": _format_product_positioning,
    }

    for filename, formatter in files.items():
        content = formatter(intelligence)
        filepath = FOUNDER_PROCESSED_DIR / filename
        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Generated: {filename}")


def generate_master_file(intelligence: FounderIntelligence, recent_posts: list[str] = None) -> None:
    """Generate the master founder_posts.md knowledge file.

    This is the ONLY file used by Founder Brain.

    Args:
        intelligence: The analyzed founder intelligence.
        recent_posts: Optional list of recent post samples.
    """
    recent_posts = recent_posts or []

    sections = [
        _format_master_header(intelligence),
        _format_writing_style_section(intelligence),
        _format_hooks_section(intelligence),
        _format_storytelling_section(intelligence),
        _format_vocabulary_section(intelligence),
        _format_philosophy_section(intelligence),
        _format_product_positioning_section(intelligence),
        _format_communication_section(intelligence),
        _format_cta_section(intelligence),
        _format_dos_donts_section(intelligence),
        _format_recent_posts(recent_posts),
    ]

    content = "\n\n".join(sections)

    FOUNDER_MASTER_FILE.parent.mkdir(parents=True, exist_ok=True)
    FOUNDER_MASTER_FILE.write_text(content, encoding="utf-8")
    logger.info(f"Generated master file: {FOUNDER_MASTER_FILE} ({len(content)} chars)")


# --- Formatting Functions ---

def _format_master_header(i: FounderIntelligence) -> str:
    return f"""# Founder Knowledge Base

**Founder:** Udit Agrawal
**Last Updated:** {i.last_updated}
**Posts Analyzed:** {i.posts_analyzed}

This file is auto-generated by the Founder Intelligence Pipeline.
Do NOT edit manually. Run `python founder_ingestion.py` to refresh."""


def _format_writing_style(i: FounderIntelligence) -> str:
    s = i.writing_style
    return f"""## Writing Style

**Avg Sentence Length:** {s.avg_sentence_length} words
**Avg Paragraph Length:** {s.avg_paragraph_length} sentences
**Tone:** {', '.join(s.tone) if s.tone else 'Direct, confident, conversational'}
**Formality:** {s.formality}
**Short Sentences:** {'Yes' if s.uses_short_sentences else 'No'}
**Uses Line Breaks:** {'Yes' if s.uses_line_breaks else 'No'}
**Uses Emojis:** {'Yes' if s.uses_emojis else 'No'}
**Uses Hashtags:** {'Yes' if s.uses_hashtags else 'No'}"""


def _format_hooks(i: FounderIntelligence) -> str:
    lines = ["# Hook Patterns\n"]
    for h in i.hook_patterns[:5]:
        lines.append(f"- **{h.pattern}** (used {h.frequency}x)")
    return "\n".join(lines)


def _format_storytelling(i: FounderIntelligence) -> str:
    return f"""# Storytelling Patterns

**Primary Pattern:** {i.storytelling_pattern}

Founder uses insight-sharing and personal anecdotes to build credibility.
Stories are grounded in real business challenges, not hypotheticals."""


def _format_vocabulary(i: FounderIntelligence) -> str:
    words = "\n".join(f"- {w}" for w in i.vocabulary[:30])
    return f"""# Vocabulary

Power words and phrases frequently used:

{words}"""


def _format_opinions(i: FounderIntelligence) -> str:
    lines = ["# Opinions\n"]
    for o in i.opinions[:10]:
        lines.append(f"- **{o.topic}:** {o.stance}")
    return "\n".join(lines)


def _format_communication(i: FounderIntelligence) -> str:
    return f"""# Communication Style

{i.communication_style}

**Key Characteristics:**
- Direct and confident
- Uses real examples
- Shares genuine opinions
- Challenges conventional thinking
- Focuses on business outcomes"""


def _format_brand_voice(i: FounderIntelligence) -> str:
    return f"""# Brand Voice

**Communication Style:** {i.communication_style}

**Tone:** {', '.join(i.writing_style.tone) if i.writing_style.tone else 'Authoritative yet approachable'}

**Positioning:** Enterprise AI infrastructure built for privacy and governance."""


def _format_cta_patterns(i: FounderIntelligence) -> str:
    lines = ["# CTA Patterns\n"]
    for cta in i.cta_patterns[:5]:
        lines.append(f"- {cta}")
    return "\n".join(lines)


def _format_product_positioning(i: FounderIntelligence) -> str:
    lines = ["# Product Positioning\n"]
    for p in i.product_positioning:
        lines.append(f"- {p}")
    return "\n".join(lines)


# --- Master File Section Formatters ---

def _format_writing_style_section(i: FounderIntelligence) -> str:
    s = i.writing_style
    return f"""## Writing Style

- Average sentence length: {s.avg_sentence_length} words
- Average paragraph length: {s.avg_paragraph_length} sentences
- Tone: {', '.join(s.tone) if s.tone else 'Direct, confident'}
- Uses short, punchy sentences: {'Yes' if s.uses_short_sentences else 'No'}
- Uses line breaks for visual appeal: {'Yes' if s.uses_line_breaks else 'No'}"""


def _format_hooks_section(i: FounderIntelligence) -> str:
    lines = ["## Hook Patterns\n"]
    for h in i.hook_patterns[:5]:
        lines.append(f"- {h.pattern}")
    return "\n".join(lines)


def _format_storytelling_section(i: FounderIntelligence) -> str:
    return f"""## Storytelling Structure

**Pattern:** {i.storytelling_pattern}

Stories ground business insight in real experience. Never hypothetical.
Always connects back to enterprise AI challenges."""


def _format_vocabulary_section(i: FounderIntelligence) -> str:
    words = ", ".join(i.vocabulary[:20])
    return f"""## Vocabulary

Power words: {words}"""


def _format_philosophy_section(i: FounderIntelligence) -> str:
    lines = ["## Business Philosophy\n"]
    for p in i.business_philosophy:
        lines.append(f"- {p}")
    return "\n".join(lines)


def _format_product_positioning_section(i: FounderIntelligence) -> str:
    lines = ["## Product Positioning\n"]
    for p in i.product_positioning:
        lines.append(f"- {p}")
    return "\n".join(lines)


def _format_communication_section(i: FounderIntelligence) -> str:
    return f"""## Communication Rules

{i.communication_style}

- Lead with business outcomes, never technology features
- Use short paragraphs (1-3 sentences)
- Challenge conventional thinking
- Share real opinions, not generic advice"""


def _format_cta_section(i: FounderIntelligence) -> str:
    lines = ["## CTA Style\n"]
    for cta in i.cta_patterns[:3]:
        lines.append(f"- {cta}")
    if not lines[1:]:
        lines.append("- Ask thought-provoking questions")
        lines.append("- Invite discussion")
    return "\n".join(lines)


def _format_dos_donts_section(i: FounderIntelligence) -> str:
    dos = "\n".join(f"- {d}" for d in i.writing_dos[:5]) if i.writing_dos else "- Be direct\n- Use real examples\n- Challenge assumptions"
    donts = "\n".join(f"- {d}" for d in i.writing_donts[:5]) if i.writing_donts else "- Use jargon\n- Be generic\n- Oversell"
    return f"""## Writing Do's

{dos}

## Writing Don'ts

{donts}"""


def _format_recent_posts(posts: list[str]) -> str:
    if not posts:
        return "## Recent Sample Posts\n\n*No posts available yet. Run founder_ingestion.py to fetch posts.*"

    samples = []
    for i, post in enumerate(posts[:5], 1):
        samples.append(f"### Post {i}\n\n{post[:500]}...")

    return "## Recent Sample Posts\n\n" + "\n\n".join(samples)

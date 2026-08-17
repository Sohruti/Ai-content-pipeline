"""Central configuration for the 2OS GTM Content Operating System."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Groq (Primary)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# Google Gemini (Fallback)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GOOGLE_MODEL = os.getenv("GOOGLE_MODEL", "gemini-2.0-flash")

# Tavily
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")

# Embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Vector Store
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", str(Path.cwd() / "data" / "faiss_index"))

# Paths
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "outputs")

# Data sources
DATA_SOURCES = {
    "website": DATA_DIR / "website" / "website.md",
    "blogs": DATA_DIR / "blogs" / "blogs.md",
    "founder_posts": DATA_DIR / "founder_posts" / "founder_posts.md",
    "customer_stories": DATA_DIR / "customer_stories" / "customer_stories.md",
    "product": DATA_DIR / "product" / "product.md",
}

# Founder Configuration
FOUNDER_NAME = "Udit Agrawal"
FOUNDER_LINKEDIN_URL = "https://www.linkedin.com/in/udit003/"
FOUNDER_POSTS_DIR = DATA_DIR / "founder_posts"
FOUNDER_RAW_DIR = FOUNDER_POSTS_DIR / "raw"
FOUNDER_PROCESSED_DIR = FOUNDER_POSTS_DIR / "processed"
FOUNDER_MASTER_FILE = FOUNDER_POSTS_DIR / "founder_posts.md"

# Review thresholds
MIN_REVIEW_SCORE = 9
MAX_REVIEW_ITERATIONS = 3

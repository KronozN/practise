from pathlib import Path
import zipfile, textwrap, json, os

base=Path(__file__).parent
base.mkdir(exist_ok=True)

files ={
    "README.md": textwrap.dedent("""\
        # Sample Package

        This is a sample package created for demonstration purposes.
        A clean starter codebase for a Retrieval-Augmented Generation system with:

        - Query Processing Layer
        - Vector Retrieval Layer
        - Re-ranking Layer
        - Generation Layer
        - Evaluation Layer

        ## Tech Stack

        - Python
        - FastAPI
        - ChromaDB
        - SentenceTransformers
        - CrossEncoder re-ranker
        - OpenAI-compatible LLM API

        ## Setup

        ```bash
        python -m venv venv
        source venv/bin/activate   # macOS/Linux
        pip install -r requirements.txt
    """),
}
    
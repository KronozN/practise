import argparse
import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter


SUPPORTED_EXTENSIONS = [".pdf", ".txt", ".md"]


def check_environment() -> None:
    """Load environment variables and check API key."""
    load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise EnvironmentError(
            "OPENAI_API_KEY is missing. Create a .env file with OPENAI_API_KEY=your_api_key_here"
        )


def load_documents(data_path: str) -> List[Document]:
    """
    Load PDF, TXT, and Markdown documents from a folder.

    Args:
        data_path: Path to the folder containing documents.

    Returns:
        A list of LangChain Document objects.
    """
    folder = Path(data_path)

    if not folder.exists():
        raise FileNotFoundError(f"Data folder not found: {data_path}")

    documents: List[Document] = []

    pdf_loader = DirectoryLoader(
        str(folder),
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
        show_progress=True,
    )
    documents.extend(pdf_loader.load())

    for extension in [".txt", ".md"]:
        text_loader = DirectoryLoader(
            str(folder),
            glob=f"**/*{extension}",
            loader_cls=TextLoader,
            loader_kwargs={"encoding": "utf-8"},
            show_progress=True,
        )
        documents.extend(text_loader.load())

    if not documents:
        raise ValueError(
            f"No supported files found in {data_path}. Add PDF, TXT, or MD files."
        )

    return documents


def split_documents(
    documents: List[Document],
    chunk_size: int = 900,
    chunk_overlap: int = 150,
) -> List[Document]:
    """
    Split documents into smaller chunks for retrieval.

    Args:
        documents: Loaded documents.
        chunk_size: Maximum chunk size.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        A list of document chunks.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""],
    )

    return splitter.split_documents(documents)


def build_or_load_vector_store(
    chunks: List[Document],
    persist_directory: str = "./chroma_db",
    rebuild: bool = False,
) -> Chroma:
    """
    Build or load a Chroma vector database.

    Args:
        chunks: Document chunks to index.
        persist_directory: Local path for Chroma database.
        rebuild: If True, rebuilds the database from scratch.

    Returns:
        Chroma vector store.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    db_path = Path(persist_directory)

    if db_path.exists() and not rebuild:
        print(f"Loading existing vector database from: {persist_directory}")
        return Chroma(
            persist_directory=persist_directory,
            embedding_function=embeddings,
        )

    print("Building new vector database...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_directory,
    )

    return vector_store


def create_rag_chain(vector_store: Chroma):
    """
    Create the retrieval and generation pipeline.

    Args:
        vector_store: Chroma vector store.

    Returns:
        A callable RAG function.
    """
    retriever = vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 5},
    )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
    )

    prompt = ChatPromptTemplate.from_template(
        """
You are a careful research assistant.

Answer the question using only the provided context.
If the answer is not available in the context, say:
"The provided documents do not contain enough information to answer this."

Use clear British English.

Context:
{context}

Question:
{question}

Answer:
"""
    )

    def rag_answer(question: str) -> dict:
        retrieved_docs = retriever.invoke(question)

        context = "\n\n".join(
            [
                f"Source: {doc.metadata.get('source', 'Unknown')}\n{doc.page_content}"
                for doc in retrieved_docs
            ]
        )

        response = llm.invoke(
            prompt.format_messages(
                context=context,
                question=question,
            )
        )

        sources = sorted(
            {
                doc.metadata.get("source", "Unknown")
                for doc in retrieved_docs
            }
        )

        return {
            "answer": response.content,
            "sources": sources,
            "retrieved_chunks": retrieved_docs,
        }

    return rag_answer


def run_rag(
    data_path: str,
    question: str,
    db_path: str,
    rebuild: bool,
) -> None:
    """Run the complete RAG pipeline."""
    check_environment()

    documents = load_documents(data_path)
    print(f"Loaded documents: {len(documents)}")

    chunks = split_documents(documents)
    print(f"Created chunks: {len(chunks)}")

    vector_store = build_or_load_vector_store(
        chunks=chunks,
        persist_directory=db_path,
        rebuild=rebuild,
    )

    rag_chain = create_rag_chain(vector_store)
    result = rag_chain(question)

    print("\n" + "=" * 80)
    print("ANSWER")
    print("=" * 80)
    print(result["answer"])

    print("\n" + "=" * 80)
    print("SOURCES")
    print("=" * 80)
    for source in result["sources"]:
        print(f"- {source}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Simple RAG application using LangChain, OpenAI, and Chroma."
    )

    parser.add_argument(
        "--data",
        type=str,
        default="./data",
        help="Folder containing PDF, TXT, or Markdown files.",
    )

    parser.add_argument(
        "--question",
        type=str,
        required=True,
        help="Question to ask over the documents.",
    )

    parser.add_argument(
        "--db",
        type=str,
        default="./chroma_db",
        help="Folder for storing the Chroma vector database.",
    )

    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the vector database from scratch.",
    )

    args = parser.parse_args()

    run_rag(
        data_path=args.data,
        question=args.question,
        db_path=args.db,
        rebuild=args.rebuild,
    )


if __name__ == "__main__":
    main()

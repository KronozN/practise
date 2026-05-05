from pathlib import Path
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from transformers import pipeline


def load_text_files(folder="data"):
    texts = []
    for file in Path(folder).glob("*.txt"):
        texts.append(file.read_text(encoding="utf-8"))
    return "\n\n".join(texts)


def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks


def build_vector_store(chunks):
    embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    embeddings = embedding_model.encode(chunks)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(embeddings)

    return index, embedding_model


def retrieve(query, chunks, index, embedding_model, top_k=3):
    query_embedding = embedding_model.encode([query])
    query_embedding = np.array(query_embedding).astype("float32")

    distances, indices = index.search(query_embedding, top_k)

    retrieved_chunks = [chunks[i] for i in indices[0]]
    return retrieved_chunks


def generate_answer(query, retrieved_chunks):
    context = "\n\n".join(retrieved_chunks)

    generator = pipeline(
        "text2text-generation",
        model="google/flan-t5-small"
    )

    prompt = f"""
Answer the question using only the context below.

Context:
{context}

Question:
{query}

Answer:
"""

    response = generator(prompt, max_new_tokens=150)
    return response[0]["generated_text"]


def main():
    print("Loading documents...")
    text = load_text_files("data")

    print("Splitting text...")
    chunks = chunk_text(text)

    print("Creating local embeddings...")
    index, embedding_model = build_vector_store(chunks)

    while True:
        query = input("\nAsk a question, or type 'exit': ")

        if query.lower() == "exit":
            break

        retrieved_chunks = retrieve(
            query=query,
            chunks=chunks,
            index=index,
            embedding_model=embedding_model,
            top_k=3
        )

        answer = generate_answer(query, retrieved_chunks)

        print("\nAnswer:")
        print(answer)

        print("\nRetrieved context:")
        for i, chunk in enumerate(retrieved_chunks, start=1):
            print(f"\n--- Chunk {i} ---")
            print(chunk[:500])


if __name__ == "__main__":
    main()
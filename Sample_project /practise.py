from dotenv import load_dotenv
import os

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI

from langchain.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings

load_dotenv()
openai_api_keys = os.getenv("OPENAI_API_KEY")

def setup_rag_system():
    loader = TextLoader("/data/user-manual.pdf")
    documents = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    document_chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings(openai_api_keys=openai_api_keys)

    vector_store = FAISS.from_documents(document_chunks, embeddings)

    retriever = vector_store.as_retreiver(
        search_type = "similarity",
        search_kwargs = {"k":5}
    )
    return retriever

async def get_rag_response(query:str):
    retriever = setup_rag_system()
    
   # Retrieve the relevant documents using 'get_relevant_documents' method
   retrieved_docs = retriever.get_relevant_documents(query)

   # Prepare the input for the LLM: Combine the query and the retrieved documents into a single string
   context = "\n".join([doc.page_content for doc in retrieved_docs])

   # LLM expects a list of strings (prompts), so we create one by combining the query with the retrieved context
   prompt = [f"Use the following information to answer the question:\n\n{context}\n\nQuestion: {query}"]

   # Generate the final response using the language model (LLM)
   generated_response = llm.generate(prompt)
  
   return generated_response


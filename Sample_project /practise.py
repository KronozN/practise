from dotenv import load_dotenv
import os

from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAI
from langchain.chains import RetrievalQA
from langchain.vectorstores import FAISS
from langchain_openai.embeddings import OpenAIEmbeddings

load_dotenv()
openai_api_keys = os.getenv("OPENAI_API_KEY")

loader = TextLoader("/data/user-manual.pdf")
documents = loader.load()

splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
document_chunks = splitter.split_documents(documents)

embeddings=OpenAIEmbeddings

vector_store = FAISS.from_documents(document_chunks, embeddings)

retriever = vector_store.as_retreiver(
    search_type = "similarity",
    search_kwargs = {"k":5}
)

llm =OpenAI(openai_api_keys=openai_api_keys)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
)

query = "what is the usermanual about?"
response = qa_chain.invoke({"query": query})

print(response)


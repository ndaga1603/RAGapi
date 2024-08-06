from langchain_community.vectorstores import Chroma
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_cohere import CohereEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.llms import Ollama
from langchain_cohere import ChatCohere
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
)
from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

from dotenv import load_dotenv
load_dotenv()
import os


class RAGpdf:
    embedding = CohereEmbeddings(cohere_api_key=os.getenv("COHERE_API_KEY"))
    llm = ChatCohere(cohere_api_key=os.getenv("COHERE_API_KEY"))
    database_name = "ChromaDB"
    template = """
    You are an AI assistant for a company that offers specialized services to its customers. Your goal is to provide accurate and concise answers based on the given context and chat history. Follow these guidelines:

    1. Use the provided context and chat history to formulate your response.
    2. Ensure your answer is clear, concise, and directly related to the provided context.
    3. If the question is not relevant to the provided context, respond with: "I'm sorry, but I can only answer questions related to the provided context. Please provide more information or ask a related question."
    
    Context: {context}
    Chat History: {history}
    Question: {question}
    
    """
    prompt = PromptTemplate(
        input_variables=["context", "history", "question"],
        output_variables=["answer"],
        template=template,
    )
    def document_loader(self, document_path):
        # loader = DirectoryLoader(document_path)
        loader = PyPDFLoader(document_path)
        documents = loader.load()
        return documents

    def text_splitter(self, documents):
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        texts = text_splitter.split_documents(documents)
        return texts

    def create_vectorstore_db(self, texts, collection_name):
        vectorstore = Chroma.from_documents(
            collection_name=collection_name,
            documents=texts, embedding=self.embedding, persist_directory=self.database_name
        )
        vectorstore.persist()
        vectorstore = None

    def load_vectorstore_db(self, collection_name):
        vectorstore = Chroma(
            persist_directory=self.database_name, 
            embedding_function=self.embedding, 
            collection_name=collection_name
        )
        return vectorstore

    def delete_collection(self, collection_name):
        try:
            Chroma.delete_collection(collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection '{collection_name}': {e}")
            return False

    # def update_collection(self, collection_name, new_documents):
    #     try:
    #         Chroma.delete_collection(collection_name)  # Delete existing collection
    #         # Create and persist new collection
    #         vectorstore = Chroma.from_documents(
    #             collection_name=collection_name,
    #             documents=new_documents,
    #             embedding=self.embedding,
    #             persist_directory=self.database_name,
    #         )
    #         vectorstore.persist()
    #         return True
    #     except Exception as e:
    #         print(f"Error updating collection '{collection_name}': {e}")
    #         return False

    def create_chain(self, vectorstore):
        memory = ConversationBufferMemory(memory_key="history", input_key="question")
        chain = RetrievalQA.from_chain_type(
            self.llm,
            retriever = MultiQueryRetriever.from_llm(
                retriever=vectorstore.as_retriever(),
                llm=self.llm,
            ),
            chain_type = "stuff",
            chain_type_kwargs = {"prompt": self.prompt, "memory": memory},
        )
        return chain

    def get_answer(self, chain, question):
        return chain.invoke(question)

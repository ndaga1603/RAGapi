from flask import Flask, request
from flask_restful import Resource, Api
from rag import RAGpdf
import threading
import queue

app = Flask(__name__)
api = Api(app)
rag = RAGpdf()

class ChatAPI(Resource):
    def __init__(self):
        self.response_queue = queue.Queue()
        
    def post(self):
        # Extracting data from the request
        question = request.form["question"]
        collection_name = request.form["collection_name"]

        # Creating a thread to handle the request asynchronously
        thread = threading.Thread(target=self.process_chat_request, args=(question, collection_name))
        thread.start()

        # Waiting for the response to be available in the queue
        response = self.response_queue.get()

        # Responding to the client with the received response
        return response


    def process_chat_request(self, question, collection_name):
        # Handling the request in a separate thread
        vectorstore = rag.load_vectorstore_db(collection_name=collection_name)
        chain = rag.create_chain(vectorstore)
        response = rag.get_answer(chain=chain, question=question)
        # Put the response into the queue for the main thread to pick up
        self.response_queue.put(response)

class DatabaseAPI(Resource):
    def post(self):
        # Extracting data from the request
        document = request.files["document"]
        collection_name = request.form["collection_name"]
        
        # Creating a thread to handle the request asynchronously
        thread = threading.Thread(target=self.process_database_request, args=(document, collection_name))
        thread.start()
        
        # Responding to the client immediately
        return {"message": "Request received and is being processed"}

    def process_database_request(self, document, collection_name):
        # Handling the request in a separate thread
        document_path = document.filename
        document.save(f"Documents/{document_path}")
        document.close()    
        documents = rag.document_loader(f"Documents/{document_path}")
        texts = rag.text_splitter(documents)
        rag.create_vectorstore_db(texts, collection_name)
        return {"message": f"Database {collection_name} created successfully"}

api.add_resource(ChatAPI, "/chat")
api.add_resource(DatabaseAPI, "/database")

if __name__ == "__main__":
    app.run(debug=True, threaded=True)

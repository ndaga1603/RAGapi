from flask import Flask, request, jsonify
from flasgger import Swagger
from prometheus_client import Summary, Counter, Gauge
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app
import requests
import logging
from flask_restful import Resource, Api
from rag import RAGpdf
import threading
import queue
import os
import time
import multiprocessing
import communications as comm
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_TIME = Summary("request_processing_seconds", "Time spent processing request")
REQUEST_COUNTER = Counter("http_requests_total", "Total number of HTTP requests")
ERROR_COUNTER = Counter("http_errors_total", "Total number of HTTP errors")
IN_PROGRESS = Gauge("inprogress_requests", "Number of requests in progress")


app = Flask(__name__)
swagger = Swagger(app, template_file="swagger.yml")


# Add prometheus wsgi middleware to route /metrics requests
app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {"/metrics": make_wsgi_app()})

api = Api(app)
rag = RAGpdf()

telegram_channel = None


class ChatAPI(Resource):

    @REQUEST_TIME.time()
    @REQUEST_COUNTER.count_exceptions()
    @IN_PROGRESS.track_inprogress()
    
    def __init__(self):
        self.response_queue = queue.Queue()

    def post(self):
        # Extracting data from the request
        question = request.get_json()["question"]
        collection_name = request.get_json()["collection_name"]

        logger.info(
            f"Received chat request: question={question}, collection_name={collection_name}"
        )

        # Creating a thread to handle the request asynchronously
        thread = threading.Thread(
            target=self.process_chat_request, args=(question, collection_name)
        )
        thread.start()

        # Waiting for the response to be available in the queue
        response = self.response_queue.get()

        # Responding to the client with the received response
        return response

    def process_chat_request(self, question, collection_name):
        start_time = time.time()
        # Handling the request in a separate thread
        try:
            vectorstore = rag.load_vectorstore_db(collection_name=collection_name)
            chain = rag.create_chain(vectorstore)
            response = rag.get_answer(chain=chain, question=question)
            # Put the response into the queue for the main thread to pick up
            self.response_queue.put(response)
            logger.info(f"Processed chat request: question={question}, response={response}")
        except Exception as e:
            logger.error(f"Error processing chat request: {e}")
        finally:
            elapsed_time = time.time() - start_time
            logger.info(f"Chat request processed in {elapsed_time} seconds")


class DatabaseAPI(Resource):
    def post(self):
        try:
            # Extracting data from the request
            document = request.files["document"]
            collection_name = request.form["collection_name"]

            # Save the document immediately to ensure it's properly uploaded
            document_path = os.path.join("Documents", document.filename)
            os.makedirs("Documents", exist_ok=True)
            document.save(document_path)
            document.close()

            # Verify if the file is saved and not empty
            if not os.path.exists(document_path):
                raise ValueError("The file was not saved correctly")
            if os.path.getsize(document_path) == 0:
                raise ValueError("The uploaded file is empty")

            # Creating a queue to communicate the result back from the thread
            result_queue = queue.Queue()

            # Creating a thread to handle the request asynchronously
            thread = threading.Thread(
                target=self.process_database_request,
                args=(document_path, collection_name, result_queue),
            )
            thread.start()
            thread.join()  # Wait for the thread to finish

            # Get the result from the queue
            result = result_queue.get()

            # Responding to the client with the result
            return jsonify(result)
        except Exception as e:
            # Log the error and handle exceptions
            print(f"Error during document upload: {e}")
            logger.error(f"Error during document upload: {e}")
            return {"message": f"Failed to upload document: {str(e)}"}, 500

    def process_database_request(self, document_path, collection_name, result_queue):
        try:
            # Handling the request in a separate thread
            documents = rag.document_loader(document_path)
            texts = rag.text_splitter(documents)
            rag.create_vectorstore_db(texts, collection_name)
            message = {"message": f"Database {collection_name} created successfully"}
        except Exception as e:
            message = {
                "message": f"Failed to create database {collection_name}: {str(e)}"
            }

        # Put the result message into the queue
        result_queue.put(message)


class SetupTelegramBot(Resource):
    def post(self):
        data = request.get_json()
        token = data.get("token")
        bot_username = data.get("bot_username")
        initial_text = data.get("initial_text")
        help_text = data.get("help_text")

        if not initial_text:
            initial_text = "Welcome, please let me know how I can assist you."

        if not help_text:
            help_text = "You can ask me anything about this Organization and I will try to answer your questions."

        if not token:
            return {"error": "Token is required"}, 400

        global telegram_channel
        telegram_channel = comm.TelegramChannel()
        telegram_channel.setup(
            token=token,
            initial_text=initial_text,
            help_text=help_text,
            bot_username=bot_username,
        )

        # Set the webhook URL
        webhook_url = os.getenv("WEBHOOK_URL")
        response = requests.get(
            f"https://api.telegram.org/bot{token}/setWebhook?url={webhook_url}"
        )
        print(response)
        logger.info(f"Setting webhook: {response.status_code}, {response.text}")
        if response.status_code != 200:
            return {"error": "Failed to set webhook"}, 500

        # Start the polling in a separate process
        telegram_process = multiprocessing.Process(
            target=telegram_channel.start_polling
        )
        telegram_process.start()

        return {"message": "Telegram Bot set up successfully"}


api.add_resource(ChatAPI, "/chat")
api.add_resource(DatabaseAPI, "/database")
api.add_resource(SetupTelegramBot, "/setup_telegram_bot")

if __name__ == "__main__":
    DEBUG = os.getenv("DEBUG", False)
    app.run(debug=DEBUG)

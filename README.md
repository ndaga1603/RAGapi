# Flask Application with RAGpdf and Telegram Integration

## Overview

This documentation provides a detailed overview of a Flask-based application designed to handle chat interactions, document uploads, and Telegram bot integration. The system utilizes asynchronous processing for handling requests and leverages the LangChain library for document processing and query answering.

- **Note: The documentation is found at /apidocs/**

## System Components

### Flask Application (main.py)

The Flask application serves as the backend server, providing RESTful API endpoints for various functionalities. The main components are:

1. *ChatAPI*: Handles chat requests asynchronously by processing user questions and fetching answers from a pre-loaded vector store database.
2. *DatabaseAPI*: Manages document uploads, processes the documents to create a vector store database, and ensures the documents are properly saved and indexed.
3. *SetupTelegramBot*: Configures and initiates a Telegram bot to interact with users, allowing them to ask questions and receive answers based on the document database.

### RAGpdf Class (rag.py)

The RAGpdf class is responsible for handling document processing and query answering using the LangChain library. Key features include:

1. *Document Loader*: Loads PDF documents for processing.
2. *Text Splitter*: Splits loaded documents into manageable chunks for indexing.
3. *Vector Store Creation*: Creates and persists a vector store database from the text chunks.
4. *Vector Store Loading*: Loads an existing vector store database for query answering.
5. *Chain Creation*: Creates a query-answering chain using the LangChain library.
6. *Answer Retrieval*: Retrieves answers to user questions based on the vector store database.

### TelegramChannel Class (telegram_channel.py)

The TelegramChannel class sets up and manages a Telegram bot for user interactions. It handles incoming messages, processes questions, and responds with answers. Key functionalities include:

1. *Setup*: Initializes the Telegram bot with token, initial text, help text, and bot username.
2. *Command Handlers*: Handles /start and /help commands to provide users with information and guidance.
3. *Message Handler*: Processes incoming messages and generates responses by querying the vector store database.
4. *Error Handling*: Manages errors that occur during bot interactions.
5. *Polling Management*: Starts and stops the bot's polling process to handle messages in real-time.

## How It Works

### 1. Initialization

- *Environment Variables*: The application relies on environment variables (defined in a .env file) for API keys and webhook URLs. These are loaded at the start of the application.
- *Flask Setup*: The Flask application is initialized, and API resources are added to handle chat, database, and Telegram bot setup requests.

### 2. Handling Chat Requests

- *ChatAPI*: When a chat request is received, it extracts the question and collection name from the request form.
- *Asynchronous Processing*: A separate thread is created to process the chat request asynchronously, ensuring the main thread remains responsive.
- *Query Processing*: The RAGpdf class loads the relevant vector store database, creates a query-answering chain, and retrieves the answer.
- *Response Delivery*: The processed answer is put into a queue and returned to the client.

### 3. Handling Document Uploads

- *DatabaseAPI*: When a document upload request is received, it extracts the document and collection name from the request.
- *Document Saving*: The document is saved to a specified directory, and its existence and size are verified.
- *Asynchronous Processing*: A separate thread processes the document, splitting it into text chunks and creating a vector store database.
- *Response Delivery*: The result of the database creation is put into a queue and returned to the client.

### 4. Setting Up Telegram Bot

- *SetupTelegramBot*: When a request to set up the Telegram bot is received, it extracts the necessary details (token, initial text, help text, bot username) from the request JSON.
- *Bot Initialization*: The TelegramChannel class is instantiated, and the bot is set up with the provided details.
- *Webhook Configuration*: The Telegram bot's webhook URL is set using the Telegram API.
- *Polling Start*: A separate process is started to handle the bot's polling, allowing it to receive and respond to messages in real-time.

### 5. Telegram Bot Interaction

- *Command Handlers*: The bot responds to /start and /help commands with predefined messages.
- *Message Handling*: When a user sends a message, the bot processes the question, queries the vector store database, and sends the answer back to the user.
- *Group Chats*: In group chats, the bot responds only when mentioned, ensuring it doesn't interfere with general conversations.

## API Endpoints

### 1. ChatAPI

*Endpoint*: `/chat`

*Method*: `POST`

*Description*: Handles chat requests asynchronously. Processes a user's question and retrieves an answer from a pre-loaded vector store database.

*Required Inputs*:

- `question`: The question to be answered.
- `collection_name`: The name of the collection (vector store database) to query.

*Example Request*:

`curl -X POST "http://127.0.0.1:5000/chat" -H  "accept: application/json" -H  "Content-Type: application/json" -d "{  \"collection_name\": \"dit_prospectus\",  \"question\": \"where is DIT located in dar es salaam?\"}"`

*Example Response*:

``` json
{
  "query": "where is DIT located in dar es salaam?",
  "result": "DIT is located in the Dar es Salaam city centre, at the junction of Morogoro Road and Bibi Titi Mohamed Street."
}
```

### 2. DatabaseAPI

*Endpoint*: `/database`

*Method*: `POST`

*Description*: Manages document uploads. Processes the uploaded document to create a vector store database.

*Required Inputs*:

- `document`: The document file to be uploaded (sent as multipart/form-data).
- `collection_name`: The name of the collection to be created in the vector store database.

*Example Request*:

`http
POST /database
Content-Type: multipart/form-data
document=@path/to/document.pdf&collection_name=new_documents
`
*Example Response*:

```json
{
  "message": "Database new_documents created successfully"
}
```

### 3. SetupTelegramBot

*Endpoint*: `/setup_telegram_bot`

*Method*: `POST`

*Description*: Sets up a Telegram bot with the specified configuration details. Configures the bot's webhook and starts polling for messages.

*Required Inputs*:

- `token`: The Telegram bot token.
- `bot_username`: (Optional) The username of the Telegram bot.
- `initial_text`: (Optional) The initial message sent to users when they start a conversation with the bot.
- `help_text`: (Optional) The message sent to users when they ask for help.

*Example Request*:

`http
POST /setup_telegram_bot
Content-Type: application/json
`

```json
{
    "token": "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
    "bot_username": "MyBot",
    "initial_text": "Welcome, how can I assist you today?",
    "help_text": "You can ask me anything about this Organization and I will try to answer your questions."
}
```

*Example Response*:

```json
{
  "message": "Telegram Bot set up successfully"
}
```

## Summary of Inputs and Outputs (API Endpoints)

### /chat

- *Inputs*:
  - `question` (string): The question to be answered.
  - `collection_name` (string): The name of the vector store database to query.
- *Outputs*:
  - result (string): The answer to the question.

### /database

- *Inputs*:
  - `document` (file): The document file to be uploaded.
  - `collection_name` (string): The name of the collection to be created.
- *Outputs*:
  - message (string): The result of the database creation process.

### /setup_telegram_bot

- *Inputs*:
  - `token` (string): The Telegram bot token.
  - `bot_username` (string, optional): The username of the Telegram bot.
  - `initial_text` (string, optional): The initial message sent to users.
  - `help_text` (string, optional): The help message sent to users.
- *Outputs*:
  - message (string): The result of the Telegram bot setup process.
  
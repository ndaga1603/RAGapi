import asyncio
from telegram import Update
from telegram.ext import (
    CommandHandler,
    MessageHandler,
    filters,
    Application,
    ContextTypes,
)
from rag import RAGpdf


class TelegramChannel:
    def __init__(self):
        self.app = None
        self.rag = RAGpdf()

    def setup(
        self, token: str, initial_text: str, help_text: str, bot_username: str = None
    ):
        self.initial_text = initial_text
        self.bot_username = bot_username
        self.help_text = help_text
        self.app = Application.builder().token(token).build()
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(
            MessageHandler(filters.TEXT & (~filters.COMMAND), self.handle_message)
        )
        self.app.add_error_handler(self.error)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.initial_text)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.help_text)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        message_type: str = update.message.chat.type
        question: str = update.message.text

        print(f"User ({update.message.chat.id} in {message_type}): '{question}'")
        # Process the message using ChatAPI

        collection_name = "dit_prospectus"  # Must be changed dynamically
        if message_type == "group":
            if self.bot_username in question:
                new_text = question.replace(self.bot_username, "").strip()
                response = self.process_chat_request(new_text, collection_name)
            else:
                return
        else:
            response = self.process_chat_request(question, collection_name)

        # Send the response back to the user
        print("BOT:", response)
        await update.message.reply_text(response["result"])

    def process_chat_request(self, question, collection_name):
        # Handling the request in a separate thread
        vectorstore = self.rag.load_vectorstore_db(collection_name=collection_name)
        chain = self.rag.create_chain(vectorstore)
        response = self.rag.get_answer(chain=chain, question=question)

        return response

    async def error(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        print(f"Update {update} caused error {context.error}")

    def start_polling(self):
        if self.app:
            print("Bot is running")
            self.app.run_polling()
            
    def stop_polling(self):
        if self.app:
            self.app.stop_polling()
            print("Bot is stopped")



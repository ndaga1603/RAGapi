from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from rag import RAGpdf
from dotenv import load_dotenv

load_dotenv()
import os

BOT_USERNAME = os.getenv("BOT_USERNAME")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am a bot that can answer your questions. Please ask me anything.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("You can ask me anything and I will try to answer your questions.")

async def handle_response(text: str) -> str:
    rag = RAGpdf()
    vectorstore = rag.load_vectorstore_db(collection_name=COLLECTION_NAME)
    chain = rag.create_chain(vectorstore)
    response = rag.get_answer(chain, text)
    return response["result"]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
   
    print(f"User ({update.message.chat.id} in {message_type}: '{text}')")
   
    if message_type == "group":
        if BOT_USERNAME in text:
            new_text = text.replace(BOT_USERNAME, "").strip()
            response = await handle_response(new_text)
            
        else:
            return
    else:
        response: str = await handle_response(text)
        
    print("BOT", response)
    await update.message.reply_text(response)


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await print(f"Update {update} caused error {context.error}")      

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    
    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    
    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    
    # Error handler
    app.add_error_handler(error)
    
    #Polling
    print("Bot is running")
    app.run_polling()

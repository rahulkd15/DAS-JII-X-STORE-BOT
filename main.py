import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from config import BOT_TOKEN
from database import init_db
from handlers.admin import admin_command, admin_conv_handler
from handlers.user import start_command
from handlers.callbacks import stateless_callback_router

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    # Initialize the database and directories
    init_db()

    # Build bot application
    app = Application.builder().token(BOT_TOKEN).build()

    # Add Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))

    # Add Conversation Handlers (Stateful flows for inputs inside admin panel)
    app.add_handler(admin_conv_handler)

    # Add Generic Callback Handler (for all UI navigations and non-stateful operations)
    app.add_handler(CallbackQueryHandler(stateless_callback_router))

    # Run the bot
    print("Bot is up and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
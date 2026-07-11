import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN
from database import init_db
from handlers.admin import admin_conv_handler
from handlers.user import start_command, handle_reply_keyboard
from handlers.callbacks import stateless_callback_router

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running smoothly!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()
    init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(admin_conv_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_keyboard))
    app.add_handler(CallbackQueryHandler(stateless_callback_router))
    
    print("Bot is up and running...")
    
    # YAHAN SPEED FIX KIYA HAI 👇 (Ye purane messages ignore karega aur instantly reply dega)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()

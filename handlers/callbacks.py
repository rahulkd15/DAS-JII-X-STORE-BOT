import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from config import BOT_TOKEN
from database import init_db

# YAHAN SARE IMPORTS THEEK HAIN 👇
from handlers.admin import admin_command, admin_conv_handler
from handlers.user import start_command, handle_reply_keyboard
from handlers.callbacks import stateless_callback_router

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- DUMMY WEB SERVER FOR RAILWAY ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running smoothly!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy server running on port {port}")
    server.serve_forever()
# ------------------------------------

def main():
    # Start Dummy server for Railway
    threading.Thread(target=run_dummy_server, daemon=True).start()
    
    # Init Database
    init_db()
    
    # Build Bot
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))

    # Conversation Handlers (Admin panel inputs)
    app.add_handler(admin_conv_handler)

    # Handle Bottom Reply Keyboard Buttons (Niche wale buttons ke liye)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_keyboard))

    # Generic Callbacks (Inline buttons ke liye)
    app.add_handler(CallbackQueryHandler(stateless_callback_router))

    print("Bot is up and running...")
    app.run_polling()

if __name__ == "__main__":
    main()

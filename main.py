import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import BOT_TOKEN
from database import init_db
from handlers.admin import admin_command, admin_conv_handler
from handlers.user import start_command
from handlers.callbacks import stateless_callback_router

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- NAKLI (DUMMY) WEB SERVER RAILWAY KO TRICK KARNE KE LIYE ---
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Bot is running smoothly!")

def run_dummy_server():
    # Railway automatically ek PORT deta hai, hum usko use karenge
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    print(f"Dummy web server running on port {port}")
    server.serve_forever()
# ---------------------------------------------------------------

def main():
    # Dummy server ko background thread mein start karo
    threading.Thread(target=run_dummy_server, daemon=True).start()

    # Database initialize karo
    init_db()

    # Bot application build karo
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers add karo
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(admin_conv_handler)
    app.add_handler(CallbackQueryHandler(stateless_callback_router))

    # Bot ko start karo
    print("Bot is up and running...")
    app.run_polling()

if __name__ == "__main__":
    main()

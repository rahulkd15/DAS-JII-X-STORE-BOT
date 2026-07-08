from telegram.ext import CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_approved
from handlers.keyboards import get_main_menu_kb

async def start_command(update, context):
    user_id = update.effective_user.id
    if not is_approved(user_id):
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=s_dict.get('support_link', 'https://t.me/'))]])
        await update.message.reply_text("❌ You don't have access to this bot. Please contact the admin.", reply_markup=kb)
        return

    kb = get_main_menu_kb()
    await update.message.reply_text("Welcome to the Materials Bot! Please select an option below:", reply_markup=kb)
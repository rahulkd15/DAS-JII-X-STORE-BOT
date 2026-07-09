from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_admin

# --- Main Menu Keyboard ---
def get_main_reply_kb(user_id):
    cats = execute_query("SELECT * FROM categories", fetch_all=True)
    kb = []
    row = []
    for cat in cats:
        row.append(KeyboardButton(cat['name']))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
        
    kb.append([KeyboardButton("🆘 Contact Support")])
    if is_admin(user_id):
        kb.append([KeyboardButton("👑 Admin Panel")])
        
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# --- NAYA: Admin Panel Keyboard (Ab niche aayega) ---
def get_admin_menu_kb(is_owner_flag=False):
    kb = [
        [KeyboardButton("📦 Add Materials")],
        [KeyboardButton("👤 Add User"), KeyboardButton("🚫 Remove User")],
        [KeyboardButton("📢 Announcement"), KeyboardButton("📊 Statistics")],
        [KeyboardButton("🆘 Support Settings")]
    ]
    if is_owner_flag:
        kb.append([
            KeyboardButton("👑 Add Admin"), KeyboardButton("❌ Remove Admin")
        ])
    kb.append([KeyboardButton("🔙 Back to Main Menu")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

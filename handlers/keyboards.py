from telegram import ReplyKeyboardMarkup, KeyboardButton
from database import execute_query
from utils import is_admin

def build_kb(buttons, cols=2, add_cancel=False, add_back_admin=False, add_back_main=False):
    kb, row = [], []
    for btn in buttons:
        row.append(KeyboardButton(btn))
        if len(row) == cols:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    if add_cancel: kb.append([KeyboardButton("❌ Cancel")])
    if add_back_admin: kb.append([KeyboardButton("🔙 Back to Admin Menu")])
    if add_back_main: kb.append([KeyboardButton("🔙 Back to Main Menu")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_main_reply_kb(user_id):
    cats = execute_query("SELECT name FROM categories", fetch_all=True)
    kb = build_kb([c['name'] for c in cats], cols=2)
    kb.keyboard.append([KeyboardButton("🆘 Contact Support")])
    if is_admin(user_id): kb.keyboard.append([KeyboardButton("👑 Admin Panel")])
    return kb

def get_admin_menu_kb(is_owner_flag=False):
    kb = [
        [KeyboardButton("📦 Manage Materials")],
        [KeyboardButton("👤 Add User"), KeyboardButton("🚫 Remove User")],
        [KeyboardButton("📢 Announcement"), KeyboardButton("📊 Statistics")],
        [KeyboardButton("🆘 Support Settings")]
    ]
    if is_owner_flag: kb.append([KeyboardButton("👑 Add Admin"), KeyboardButton("❌ Remove Admin")])
    kb.append([KeyboardButton("🔙 Back to Main Menu")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_manage_materials_kb():
    return build_kb(["➕ Add Material", "🗑 Delete Material", "✏️ Edit Material", "➕ Add Category"], cols=2, add_back_admin=True)

def get_support_settings_kb():
    return build_kb(["✏️ Edit Username", "🔗 Edit Link", "📝 Edit Text"], cols=2, add_back_admin=True)

def get_categories_kb(add_cancel=True):
    cats = execute_query("SELECT name FROM categories", fetch_all=True)
    return build_kb([c['name'] for c in cats], cols=2, add_cancel=add_cancel)

def get_materials_kb(cat_name, add_cancel=True, add_back_main=False):
    mats = execute_query("SELECT materials.name FROM materials JOIN categories ON materials.category_id = categories.id WHERE categories.name=?", (cat_name,), fetch_all=True)
    return build_kb([m['name'] for m in mats], cols=1, add_cancel=add_cancel, add_back_main=add_back_main)

def get_cancel_kb(): return build_kb([], add_cancel=True)
def get_yes_no_kb(): return build_kb(["✅ Yes", "❌ No"])

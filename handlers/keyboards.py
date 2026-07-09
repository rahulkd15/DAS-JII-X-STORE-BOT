from telegram import ReplyKeyboardMarkup, KeyboardButton
from database import execute_query
from utils import is_admin, is_owner

def build_kb(buttons, cols=2, add_cancel=False, add_back_main=False):
    kb, row = [], []
    for btn in buttons:
        row.append(KeyboardButton(btn))
        if len(row) == cols:
            kb.append(row)
            row = []
    if row: kb.append(row)
    
    if add_cancel: kb.append([KeyboardButton("❌ Cancel")])
    if add_back_main: kb.append([KeyboardButton("🔙 Back to Main Menu")])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# YAHAN DEKH BHAI: Saare buttons seedhe main keyboard me daal diye hain!
def get_main_reply_kb(user_id):
    cats = execute_query("SELECT name FROM categories", fetch_all=True)
    kb = []
    row = []
    
    # 1. Normal User Buttons (Courses, Hacks, etc.)
    for cat in cats:
        row.append(KeyboardButton(cat['name']))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row: kb.append(row)
        
    kb.append([KeyboardButton("🆘 Contact Support")])
    
    # 2. Admin Buttons (Seedhe typing keyboard me, Courses ke niche!)
    if is_admin(user_id):
        kb.append([KeyboardButton("📦 Add Material"), KeyboardButton("🗑 Delete Material")])
        kb.append([KeyboardButton("✏️ Edit Material"), KeyboardButton("➕ Add Category")])
        kb.append([KeyboardButton("👤 Add User"), KeyboardButton("🚫 Remove User")])
        kb.append([KeyboardButton("📢 Announcement"), KeyboardButton("📊 Statistics")])
        kb.append([KeyboardButton("🆘 Support Settings")])
        
        # 3. Owner Buttons
        if is_owner(user_id):
            kb.append([KeyboardButton("👑 Add Admin"), KeyboardButton("❌ Remove Admin")])
            
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def get_support_settings_kb():
    return build_kb(["✏️ Edit Username", "🔗 Edit Link", "📝 Edit Text"], cols=2, add_back_main=True)

def get_categories_kb(add_cancel=True):
    cats = execute_query("SELECT name FROM categories", fetch_all=True)
    return build_kb([c['name'] for c in cats], cols=2, add_cancel=add_cancel)

def get_materials_kb(cat_name, add_cancel=True, add_back_main=False):
    mats = execute_query("SELECT materials.name FROM materials JOIN categories ON materials.category_id = categories.id WHERE categories.name=?", (cat_name,), fetch_all=True)
    return build_kb([m['name'] for m in mats], cols=1, add_cancel=add_cancel, add_back_main=add_back_main)

def get_cancel_kb(): return build_kb([], add_cancel=True)
def get_yes_no_kb(): return build_kb(["✅ Yes", "❌ No"])

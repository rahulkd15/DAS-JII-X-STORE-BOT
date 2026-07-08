from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database import execute_query

def get_main_menu_kb():
    cats = execute_query("SELECT * FROM categories", fetch_all=True)
    kb = []
    
    # 2 buttons per row for dynamic categories
    row = []
    for cat in cats:
        row.append(InlineKeyboardButton(cat['name'], callback_data=f"user_cat_{cat['id']}"))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
        
    kb.append([InlineKeyboardButton("🆘 Contact Support", callback_data="user_support")])
    return InlineKeyboardMarkup(kb)

def get_admin_menu_kb(is_owner_flag=False):
    kb = [
        [InlineKeyboardButton("📦 Add Materials", callback_data="admin_materials")],
        [InlineKeyboardButton("👤 Add User", callback_data="admin_add_user"),
         InlineKeyboardButton("🚫 Remove User", callback_data="admin_rem_user")],
        [InlineKeyboardButton("📢 Announcement", callback_data="admin_broadcast"),
         InlineKeyboardButton("📊 Statistics", callback_data="admin_stats")],
        [InlineKeyboardButton("🆘 Support Settings", callback_data="admin_support")]
    ]
    if is_owner_flag:
        kb.append([
            InlineKeyboardButton("👑 Add Admin", callback_data="admin_add_admin"),
            InlineKeyboardButton("❌ Remove Admin", callback_data="admin_rem_admin")
        ])
    return InlineKeyboardMarkup(kb)
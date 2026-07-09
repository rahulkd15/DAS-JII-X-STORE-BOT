from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_admin

# --- Niche wala Typing Area Keyboard ---
def get_main_reply_kb(user_id):
    cats = execute_query("SELECT * FROM categories", fetch_all=True)
    kb = []
    
    # Categories ko 2 columns me dikhane ke liye
    row = []
    for cat in cats:
        row.append(KeyboardButton(cat['name']))
        if len(row) == 2:
            kb.append(row)
            row = []
    if row:
        kb.append(row)
        
    kb.append([KeyboardButton("🆘 Contact Support")])
    
    # MAGIC: Agar user Admin/Owner hai, toh hi usko ye Admin Panel ka button dikhega
    if is_admin(user_id):
        kb.append([KeyboardButton("👑 Admin Panel")])
        
    # resize_keyboard=True se button screen ke hisaab se chote ho jate hain
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)


# --- Admin Panel ke andar wale Inline Buttons (Ye waise hi rahenge) ---
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

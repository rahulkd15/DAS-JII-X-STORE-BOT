from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_approved, is_admin, escape_html, is_owner
from handlers.keyboards import get_main_reply_kb, get_admin_menu_kb

# --- Start Command ---
async def start_command(update, context):
    user_id = update.effective_user.id
    if not is_approved(user_id):
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=s_dict.get('support_link', 'https://t.me/'))]])
        await update.message.reply_text("❌ You don't have access to this bot. Please contact the admin.", reply_markup=kb)
        return

    # User ke role ke hisab se niche wala Keyboard bhejega
    kb = get_main_reply_kb(user_id)
    await update.message.reply_text("Welcome to the Materials Bot! Please select an option from the menu below 👇", reply_markup=kb)

# --- Niche wale Buttons ko Handle karne ka Logic ---
async def handle_reply_keyboard(update, context):
    user_id = update.effective_user.id
    text = update.message.text

    if not is_approved(user_id):
        return

    # Agar usne Admin Panel dabaya
    if text == "👑 Admin Panel":
        if not is_admin(user_id):
            return await update.message.reply_text("❌ You don't have permission.")
        kb = get_admin_menu_kb(is_owner(user_id))
        await update.message.reply_text("👑 <b>Admin Panel</b>", parse_mode='HTML', reply_markup=kb)
        return

    # Agar usne Contact Support dabaya
    if text == "🆘 Contact Support":
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = [[InlineKeyboardButton(s_dict.get('support_username', 'Support'), url=s_dict.get('support_link', 'https://t.me/'))]]
        await update.message.reply_text(f"🆘 {escape_html(s_dict.get('contact_text', 'For any issues, please contact support.'))}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        return

    # Agar usne kisi Category (jaise Courses ya Hacks) par click kiya
    cat = execute_query("SELECT id FROM categories WHERE name=?", (text,), fetch=True)
    if cat:
        cid = cat['id']
        mats = execute_query("SELECT id, name FROM materials WHERE category_id=?", (cid,), fetch_all=True)
        
        if not mats:
            await update.message.reply_text("📂 This category is currently empty.")
            return

        kb = [[InlineKeyboardButton(m['name'], callback_data=f"user_mat_{m['id']}")] for m in mats]
        await update.message.reply_text(f"📚 <b>{text} Materials:</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        return

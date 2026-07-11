from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_approved, is_admin, escape_html, is_owner
from handlers.keyboards import *

async def start_command(update, context):
    user_id = update.effective_user.id
    if not is_approved(user_id):
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=s_dict.get('support_link', 'https://t.me/'))]])
        await update.message.reply_text("❌ You don't have access to this bot.", reply_markup=kb)
        return
    await update.message.reply_text("Welcome to the Materials Bot! Please select an option 👇", reply_markup=get_main_reply_kb(user_id))

async def handle_reply_keyboard(update, context):
    user_id = update.effective_user.id
    text = update.message.text
    if not is_approved(user_id): return

    # ADMIN PANEL NAVIGATION
    if text == "👑 Admin Panel":
        if not is_admin(user_id): return
        return await update.message.reply_text("👑 <b>Admin Panel</b>\nChoose an action:", parse_mode='HTML', reply_markup=get_admin_menu_kb(is_owner(user_id)))

    if text == "🔙 Back to Main Menu":
        return await update.message.reply_text("🏠 <b>Main Menu</b>", parse_mode='HTML', reply_markup=get_main_reply_kb(user_id))
    
    if text == "🔙 Back to Admin Menu":
        if not is_admin(user_id): return
        return await update.message.reply_text("👑 <b>Admin Panel</b>", parse_mode='HTML', reply_markup=get_admin_menu_kb(is_owner(user_id)))

    # INFO BUTTONS
    if text == "🆘 Support Settings":
        if not is_admin(user_id): return
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        msg = f"🆘 <b>Support Settings</b>\n\n<b>Username:</b> {escape_html(s_dict.get('support_username'))}\n<b>Link:</b> {escape_html(s_dict.get('support_link'))}\n<b>Text:</b> {escape_html(s_dict.get('contact_text'))}"
        return await update.message.reply_text(msg, parse_mode='HTML', reply_markup=get_support_settings_kb())
    
    if text == "📊 Statistics":
        if not is_admin(user_id): return
        users = execute_query("SELECT COUNT(user_id) as count FROM users", fetch_all=True)[0]['count']
        admins = execute_query("SELECT COUNT(user_id) as count FROM admins", fetch_all=True)[0]['count']
        cats = execute_query("SELECT COUNT(id) as count FROM categories", fetch_all=True)[0]['count']
        mats = execute_query("SELECT COUNT(id) as count FROM materials", fetch_all=True)[0]['count']
        return await update.message.reply_text(f"📊 <b>Bot Statistics</b>\n\n👥 Total Users: {users}\n👑 Total Admins: {admins + 1}\n📂 Categories: {cats}\n📚 Materials: {mats}", parse_mode='HTML')
    
    if text == "🆘 Contact Support":
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = [[InlineKeyboardButton(s_dict.get('support_username', 'Support'), url=s_dict.get('support_link', 'https://t.me/'))]]
        return await update.message.reply_text(f"🆘 {escape_html(s_dict.get('contact_text', 'Contact Support:'))}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))

    # CATEGORY BROWSING
    cat = execute_query("SELECT id FROM categories WHERE name=?", (text,), fetch=True)
    if cat:
        mats = execute_query("SELECT id FROM materials WHERE category_id=?", (cat['id'],), fetch_all=True)
        if not mats: return await update.message.reply_text("📂 This category is empty.", reply_markup=get_main_reply_kb(user_id))
        return await update.message.reply_text(f"📚 <b>{text} Materials:</b>", parse_mode='HTML', reply_markup=get_materials_kb(text, add_cancel=False, add_back_main=True))

    mat = execute_query("SELECT * FROM materials WHERE name=?", (text,), fetch=True)
    if mat:
        fid, ftype = mat['file_id'], mat['file_type']
        try:
            await update.message.reply_text("⏳ Fetching material...")
            if ftype == 'text': await context.bot.send_message(chat_id=user_id, text=fid)
            elif ftype == 'document': await context.bot.send_document(chat_id=user_id, document=fid, caption=mat['name'])
            elif ftype == 'video': await context.bot.send_video(chat_id=user_id, video=fid, caption=mat['name'])
            elif ftype == 'audio': await context.bot.send_audio(chat_id=user_id, audio=fid, caption=mat['name'])
            elif ftype == 'photo': await context.bot.send_photo(chat_id=user_id, photo=fid, caption=mat['name'])
        except Exception:
            await update.message.reply_text("❌ Failed to retrieve material.")

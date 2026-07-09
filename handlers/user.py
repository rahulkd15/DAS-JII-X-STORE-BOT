from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_approved, is_admin, escape_html, is_owner
from handlers.keyboards import get_main_reply_kb, get_admin_menu_kb

async def start_command(update, context):
    user_id = update.effective_user.id
    if not is_approved(user_id):
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("Contact Admin", url=s_dict.get('support_link', 'https://t.me/'))]])
        await update.message.reply_text("❌ You don't have access to this bot. Please contact the admin.", reply_markup=kb)
        return

    kb = get_main_reply_kb(user_id)
    await update.message.reply_text("Welcome to the Materials Bot! Please select an option from the menu below 👇", reply_markup=kb)

async def handle_reply_keyboard(update, context):
    user_id = update.effective_user.id
    text = update.message.text

    if not is_approved(user_id):
        return

    # --- MAIN MENU BUTTONS ---
    if text == "👑 Admin Panel":
        if not is_admin(user_id): return await update.message.reply_text("❌ You don't have permission.")
        kb = get_admin_menu_kb(is_owner(user_id))
        await update.message.reply_text("👑 <b>Admin Panel Options:</b>", parse_mode='HTML', reply_markup=kb)
        return

    if text == "🔙 Back to Main Menu":
        kb = get_main_reply_kb(user_id)
        await update.message.reply_text("🏠 <b>Main Menu</b>", parse_mode='HTML', reply_markup=kb)
        return

    if text == "🆘 Contact Support":
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        kb = [[InlineKeyboardButton(s_dict.get('support_username', 'Support'), url=s_dict.get('support_link', 'https://t.me/'))]]
        await update.message.reply_text(f"🆘 {escape_html(s_dict.get('contact_text', 'For any issues, please contact support.'))}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        return

    # --- ADMIN PANEL BUTTONS ---
    if text == "📦 Add Materials":
        if not is_admin(user_id): return
        cats = execute_query("SELECT * FROM categories", fetch_all=True)
        kb = []
        for cat in cats:
            name = cat['name']
            cid = cat['id']
            kb.append([InlineKeyboardButton(f"➕ Add to {name}", callback_data=f"admin_addmat_{cid}")])
            kb.append([InlineKeyboardButton(f"🗑 Delete in {name}", callback_data=f"admin_delcat_{cid}"),
                       InlineKeyboardButton(f"✏️ Edit in {name}", callback_data=f"admin_editcat_{cid}")])
        kb.append([InlineKeyboardButton("➕ Add Custom Category", callback_data="admin_add_category")])
        await update.message.reply_text("📦 <b>Manage Materials & Categories</b>\nSelect an option below:", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        return

    if text == "📊 Statistics":
        if not is_admin(user_id): return
        users = execute_query("SELECT COUNT(user_id) as count FROM users", fetch_all=True)[0]['count']
        admins = execute_query("SELECT COUNT(user_id) as count FROM admins", fetch_all=True)[0]['count']
        cats = execute_query("SELECT COUNT(id) as count FROM categories", fetch_all=True)[0]['count']
        courses = execute_query("SELECT COUNT(materials.id) as count FROM materials JOIN categories ON materials.category_id = categories.id WHERE categories.name LIKE '%Course%'", fetch_all=True)[0]['count']
        hacks = execute_query("SELECT COUNT(materials.id) as count FROM materials JOIN categories ON materials.category_id = categories.id WHERE categories.name LIKE '%Hack%'", fetch_all=True)[0]['count']
        msg = f"📊 <b>Bot Statistics</b>\n\n👥 Total Approved Users: {users}\n👑 Total Admins: {admins + 1}\n📂 Total Categories: {cats}\n📚 Total Default Courses: {courses}\n💻 Total Default Hacks: {hacks}"
        await update.message.reply_text(msg, parse_mode='HTML')
        return

    if text == "🆘 Support Settings":
        if not is_admin(user_id): return
        settings = execute_query("SELECT * FROM settings", fetch_all=True)
        s_dict = {s['key']: s['value'] for s in settings}
        msg = f"🆘 <b>Support Settings</b>\n\n<b>Username:</b> {escape_html(s_dict.get('support_username'))}\n<b>Link:</b> {escape_html(s_dict.get('support_link'))}\n<b>Text:</b> {escape_html(s_dict.get('contact_text'))}"
        kb = [[InlineKeyboardButton("✏️ Edit Username", callback_data="admin_sup_uname")],
              [InlineKeyboardButton("✏️ Edit Link", callback_data="admin_sup_link")],
              [InlineKeyboardButton("✏️ Edit Text", callback_data="admin_sup_text")]]
        await update.message.reply_text(msg, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
        return

    # --- CATEGORY BUTTONS ---
    cat = execute_query("SELECT id FROM categories WHERE name=?", (text,), fetch=True)
    if cat:
        cid = cat['id']
        mats = execute_query("SELECT id, name FROM materials WHERE category_id=?", (cid,), fetch_all=True)
        if not mats:
            return await update.message.reply_text("📂 This category is currently empty.")
        kb = [[InlineKeyboardButton(m['name'], callback_data=f"user_mat_{m['id']}")] for m in mats]
        await update.message.reply_text(f"📚 <b>{text} Materials:</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))

import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_admin, is_approved, escape_html, is_owner
from handlers.keyboards import get_main_menu_kb, get_admin_menu_kb

async def stateless_callback_router(update, context):
    """Routes callbacks that do not require state management text input."""
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("admin_"):
        if not is_admin(user_id):
            return await query.answer("Forbidden", show_alert=True)
            
        if data == "admin_materials":
            cats = execute_query("SELECT * FROM categories", fetch_all=True)
            kb = []
            for cat in cats:
                name = cat['name']
                cid = cat['id']
                kb.append([InlineKeyboardButton(f"➕ Add to {name}", callback_data=f"admin_addmat_{cid}")])
                kb.append([
                    InlineKeyboardButton(f"🗑 Delete in {name}", callback_data=f"admin_delcat_{cid}"),
                    InlineKeyboardButton(f"✏️ Edit in {name}", callback_data=f"admin_editcat_{cid}")
                ])
            kb.append([InlineKeyboardButton("➕ Add Custom Category", callback_data="admin_add_category")])
            kb.append([InlineKeyboardButton("🔙 Back to Admin Panel", callback_data="admin_back")])
            await query.edit_message_text("📦 <b>Manage Materials & Categories</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
            
        elif data == "admin_stats":
            users = execute_query("SELECT COUNT(user_id) as count FROM users", fetch_all=True)[0]['count']
            admins = execute_query("SELECT COUNT(user_id) as count FROM admins", fetch_all=True)[0]['count']
            cats = execute_query("SELECT COUNT(id) as count FROM categories", fetch_all=True)[0]['count']
            courses = execute_query("SELECT COUNT(materials.id) as count FROM materials JOIN categories ON materials.category_id = categories.id WHERE categories.name LIKE '%Course%'", fetch_all=True)[0]['count']
            hacks = execute_query("SELECT COUNT(materials.id) as count FROM materials JOIN categories ON materials.category_id = categories.id WHERE categories.name LIKE '%Hack%'", fetch_all=True)[0]['count']
            text = f"📊 <b>Bot Statistics</b>\n\n👥 Total Approved Users: {users}\n👑 Total Admins: {admins + 1}\n📂 Total Categories: {cats}\n📚 Total Default Courses: {courses}\n💻 Total Default Hacks: {hacks}"
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]]))
            
        elif data == "admin_support":
            settings = execute_query("SELECT * FROM settings", fetch_all=True)
            s_dict = {s['key']: s['value'] for s in settings}
            text = f"🆘 <b>Support Settings</b>\n\n<b>Username:</b> {escape_html(s_dict.get('support_username'))}\n<b>Link:</b> {escape_html(s_dict.get('support_link'))}\n<b>Text:</b> {escape_html(s_dict.get('contact_text'))}"
            kb = [
                [InlineKeyboardButton("✏️ Edit Username", callback_data="admin_sup_uname")],
                [InlineKeyboardButton("✏️ Edit Link", callback_data="admin_sup_link")],
                [InlineKeyboardButton("✏️ Edit Text", callback_data="admin_sup_text")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
            ]
            await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
            
        elif data.startswith("admin_delcat_"):
            cid = data.split("_")[2]
            mats = execute_query("SELECT id, name FROM materials WHERE category_id=?", (cid,), fetch_all=True)
            kb = [[InlineKeyboardButton(f"❌ {m['name']}", callback_data=f"admin_delmat_{m['id']}")] for m in mats]
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_materials")])
            await query.edit_message_text("Select a material to delete:", reply_markup=InlineKeyboardMarkup(kb))
            
        elif data.startswith("admin_delmat_"):
            mat_id = data.split("_")[2]
            kb = [[InlineKeyboardButton("✅ Yes, Delete", callback_data=f"admin_confirmdel_{mat_id}"), InlineKeyboardButton("❌ No, Cancel", callback_data="admin_materials")]]
            await query.edit_message_text("⚠️ Are you sure you want to permanently delete this material?", reply_markup=InlineKeyboardMarkup(kb))
            
        elif data.startswith("admin_confirmdel_"):
            mat_id = data.split("_")[2]
            execute_query("DELETE FROM materials WHERE id=?", (mat_id,))
            await query.edit_message_text("✅ Material deleted successfully.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_materials")]]))

        elif data.startswith("admin_editcat_"):
            cid = data.split("_")[2]
            mats = execute_query("SELECT id, name FROM materials WHERE category_id=?", (cid,), fetch_all=True)
            kb = [[InlineKeyboardButton(f"✏️ {m['name']}", callback_data=f"admin_editmat_{m['id']}")] for m in mats]
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_materials")])
            await query.edit_message_text("Select a material to edit:", reply_markup=InlineKeyboardMarkup(kb))
            
        elif data.startswith("admin_editmat_"):
            mat_id = data.split("_")[2]
            kb = [
                [InlineKeyboardButton("✏️ Change Name", callback_data=f"admin_editname_{mat_id}")],
                [InlineKeyboardButton("📤 Replace File", callback_data=f"admin_editfile_{mat_id}")],
                [InlineKeyboardButton("🗂 Move Category", callback_data=f"admin_movemat_{mat_id}")],
                [InlineKeyboardButton("❌ Delete", callback_data=f"admin_delmat_{mat_id}")],
                [InlineKeyboardButton("🔙 Back", callback_data="admin_materials")]
            ]
            await query.edit_message_text("What would you like to edit?", reply_markup=InlineKeyboardMarkup(kb))

        elif data.startswith("admin_movemat_"):
            mat_id = data.split("_")[2]
            cats = execute_query("SELECT * FROM categories", fetch_all=True)
            kb = [[InlineKeyboardButton(c['name'], callback_data=f"admin_moveexec_{mat_id}_{c['id']}")] for c in cats]
            kb.append([InlineKeyboardButton("🔙 Back", callback_data="admin_materials")])
            await query.edit_message_text("Select the new category:", reply_markup=InlineKeyboardMarkup(kb))

        elif data.startswith("admin_moveexec_"):
            parts = data.split("_")
            execute_query("UPDATE materials SET category_id=? WHERE id=?", (parts[3], parts[2]))
            await query.edit_message_text("✅ Material moved successfully.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_materials")]]))

        elif data == "admin_back":
            await query.edit_message_text("👑 <b>Admin Panel</b>", parse_mode='HTML', reply_markup=get_admin_menu_kb(is_owner(user_id)))

    # USER ROUTES
    elif data.startswith("user_"):
        if not is_approved(user_id):
            return await query.answer("No access.", show_alert=True)
            
        if data.startswith("user_cat_"):
            cid = data.split("_")[2]
            mats = execute_query("SELECT id, name FROM materials WHERE category_id=?", (cid,), fetch_all=True)
            kb = [[InlineKeyboardButton(m['name'], callback_data=f"user_mat_{m['id']}")] for m in mats]
            kb.append([InlineKeyboardButton("🔙 Back to Main Menu", callback_data="user_main_menu")])
            await query.edit_message_text("📚 <b>Available Materials:</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
            
        elif data.startswith("user_mat_"):
            await query.answer("Fetching material...")
            mat_id = data.split("_")[2]
            mat = execute_query("SELECT * FROM materials WHERE id=?", (mat_id,), fetch=True)
            if not mat:
                return await query.message.reply_text("❌ Material no longer exists.")
            
            fid, ftype = mat['file_id'], mat['file_type']
            try:
                if ftype == 'text': await context.bot.send_message(chat_id=user_id, text=fid)
                elif ftype == 'document': await context.bot.send_document(chat_id=user_id, document=fid, caption=mat['name'])
                elif ftype == 'video': await context.bot.send_video(chat_id=user_id, video=fid, caption=mat['name'])
                elif ftype == 'audio': await context.bot.send_audio(chat_id=user_id, audio=fid, caption=mat['name'])
                elif ftype == 'photo': await context.bot.send_photo(chat_id=user_id, photo=fid, caption=mat['name'])
            except Exception as e:
                logging.error(f"Failed to send material: {e}")
                await query.message.reply_text("❌ Failed to retrieve material. Contact support.")
                
        elif data == "user_support":
            settings = execute_query("SELECT * FROM settings", fetch_all=True)
            s_dict = {s['key']: s['value'] for s in settings}
            kb = [[InlineKeyboardButton(s_dict.get('support_username', 'Support'), url=s_dict.get('support_link', 'https://t.me/'))],
                  [InlineKeyboardButton("🔙 Back to Main Menu", callback_data="user_main_menu")]]
            await query.edit_message_text(f"🆘 {escape_html(s_dict.get('contact_text', 'For any issues, please contact support.'))}", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
            
        elif data == "user_main_menu":
            await query.edit_message_text("Welcome to the Materials Bot! Please select an option below:", reply_markup=get_main_menu_kb())
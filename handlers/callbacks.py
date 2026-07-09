import logging
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from database import execute_query
from utils import is_admin, is_approved

async def stateless_callback_router(update, context):
    query = update.callback_query
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("admin_"):
        if not is_admin(user_id): return await query.answer("Forbidden", show_alert=True)
            
        if data == "admin_materials":
            cats = execute_query("SELECT * FROM categories", fetch_all=True)
            kb = []
            for cat in cats:
                name = cat['name']
                cid = cat['id']
                kb.append([InlineKeyboardButton(f"➕ Add to {name}", callback_data=f"admin_addmat_{cid}")])
                kb.append([InlineKeyboardButton(f"🗑 Delete in {name}", callback_data=f"admin_delcat_{cid}"),
                           InlineKeyboardButton(f"✏️ Edit in {name}", callback_data=f"admin_editcat_{cid}")])
            kb.append([InlineKeyboardButton("➕ Add Custom Category", callback_data="admin_add_category")])
            await query.edit_message_text("📦 <b>Manage Materials & Categories</b>", parse_mode='HTML', reply_markup=InlineKeyboardMarkup(kb))
            
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

    # USER ROUTES
    elif data.startswith("user_"):
        if not is_approved(user_id): return await query.answer("No access.", show_alert=True)
            
        if data.startswith("user_mat_"):
            await query.answer("Fetching material...")
            mat_id = data.split("_")[2]
            mat = execute_query("SELECT * FROM materials WHERE id=?", (mat_id,), fetch=True)
            if not mat: return await query.message.reply_text("❌ Material no longer exists.")
            
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

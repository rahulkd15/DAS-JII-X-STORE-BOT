from telegram.ext import ConversationHandler, MessageHandler, filters, CommandHandler
from config import *
from utils import is_owner, extract_file_info
from database import execute_query
from handlers.keyboards import *

async def admin_command(update, context): pass
async def cancel_flow(update, context): pass

async def handle_cancel(update, context):
    if update.message.text == "❌ Cancel":
        await update.message.reply_text("❌ Action cancelled.", reply_markup=get_main_reply_kb(update.effective_user.id))
        return True
    return False

# --- ADD MATERIAL ---
async def prompt_add_mat(update, context):
    await update.message.reply_text("Select a category to add the material to:", reply_markup=get_categories_kb())
    return WAIT_ADD_MAT_CAT
async def recv_add_mat_cat(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    cat = execute_query("SELECT id FROM categories WHERE name=?", (update.message.text,), fetch=True)
    if not cat: return WAIT_ADD_MAT_CAT
    context.user_data['temp_cat_id'] = cat['id']
    await update.message.reply_text("📤 Send the File, Text, Forwarded Message, or Link:", reply_markup=get_cancel_kb())
    return WAIT_MAT_FILE
async def recv_mat_file(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    file_id, ftype = extract_file_info(update.message)
    if not file_id: return WAIT_MAT_FILE
    context.user_data['temp_file_id'] = file_id
    context.user_data['temp_file_type'] = ftype
    await update.message.reply_text("📝 Enter the Name for this material:", reply_markup=get_cancel_kb())
    return WAIT_MAT_NAME
async def recv_mat_name(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    execute_query("INSERT INTO materials (name, category_id, file_id, file_type) VALUES (?, ?, ?, ?)", 
                  (update.message.text, context.user_data['temp_cat_id'], context.user_data['temp_file_id'], context.user_data['temp_file_type']))
    await update.message.reply_text("✅ Material Added Successfully!", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

# --- DELETE MATERIAL ---
async def prompt_del_mat(update, context):
    await update.message.reply_text("Select a category to delete from:", reply_markup=get_categories_kb())
    return WAIT_DEL_MAT_CAT
async def recv_del_mat_cat(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    cat = execute_query("SELECT id FROM categories WHERE name=?", (update.message.text,), fetch=True)
    if not cat: return WAIT_DEL_MAT_CAT
    await update.message.reply_text("Select material to delete:", reply_markup=get_materials_kb(update.message.text))
    return WAIT_DEL_MAT_NAME
async def recv_del_mat_name(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    mat = execute_query("SELECT id FROM materials WHERE name=?", (update.message.text,), fetch=True)
    if not mat: return WAIT_DEL_MAT_NAME
    context.user_data['del_mat_id'] = mat['id']
    await update.message.reply_text(f"⚠️ Are you sure you want to delete '{update.message.text}'?", reply_markup=get_yes_no_kb())
    return WAIT_DEL_CONFIRM
async def recv_del_confirm(update, context):
    if update.message.text == "✅ Yes":
        execute_query("DELETE FROM materials WHERE id=?", (context.user_data['del_mat_id'],))
        await update.message.reply_text("✅ Deleted.", reply_markup=get_main_reply_kb(update.effective_user.id))
    else: await update.message.reply_text("❌ Cancelled.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

# --- EDIT MATERIAL ---
async def prompt_edit_mat(update, context):
    await update.message.reply_text("Select category:", reply_markup=get_categories_kb())
    return WAIT_EDIT_MAT_CAT
async def recv_edit_mat_cat(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    await update.message.reply_text("Select material to edit:", reply_markup=get_materials_kb(update.message.text))
    return WAIT_EDIT_MAT_NAME
async def recv_edit_mat_name(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    mat = execute_query("SELECT id FROM materials WHERE name=?", (update.message.text,), fetch=True)
    if not mat: return WAIT_EDIT_MAT_NAME
    context.user_data['edit_mat_id'] = mat['id']
    await update.message.reply_text("What to edit?", reply_markup=build_kb(["✏️ Change Name", "📤 Replace File", "🗂 Move Category"], add_cancel=True))
    return WAIT_EDIT_ACTION
async def recv_edit_action(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    if update.message.text == "✏️ Change Name":
        await update.message.reply_text("📝 Send new name:", reply_markup=get_cancel_kb())
        return WAIT_EDIT_NAME_NEW
    elif update.message.text == "📤 Replace File":
        await update.message.reply_text("📤 Send new file/link:", reply_markup=get_cancel_kb())
        return WAIT_EDIT_FILE_NEW
    elif update.message.text == "🗂 Move Category":
        await update.message.reply_text("Select new category:", reply_markup=get_categories_kb())
        return WAIT_EDIT_MOVE_CAT
    return WAIT_EDIT_ACTION
async def recv_edit_name_new(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    execute_query("UPDATE materials SET name=? WHERE id=?", (update.message.text, context.user_data['edit_mat_id']))
    await update.message.reply_text("✅ Name updated.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END
async def recv_edit_file_new(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    file_id, ftype = extract_file_info(update.message)
    if not file_id: return WAIT_EDIT_FILE_NEW
    execute_query("UPDATE materials SET file_id=?, file_type=? WHERE id=?", (file_id, ftype, context.user_data['edit_mat_id']))
    await update.message.reply_text("✅ File replaced.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END
async def recv_edit_move_cat(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    cat = execute_query("SELECT id FROM categories WHERE name=?", (update.message.text,), fetch=True)
    if not cat: return WAIT_EDIT_MOVE_CAT
    execute_query("UPDATE materials SET category_id=? WHERE id=?", (cat['id'], context.user_data['edit_mat_id']))
    await update.message.reply_text("✅ Moved successfully.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

# --- OTHERS ---
async def prompt_add_cat(update, context):
    await update.message.reply_text("📝 Enter new category name:", reply_markup=get_cancel_kb())
    return WAIT_CAT_NAME
async def recv_cat_name(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    execute_query("INSERT INTO categories (name) VALUES (?)", (update.message.text,))
    await update.message.reply_text("✅ Category created.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_add_user(update, context):
    await update.message.reply_text("👤 Send User ID to add:", reply_markup=get_cancel_kb())
    return WAIT_USER_ID
async def handle_add_user(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    try: execute_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (int(update.message.text),))
    except: pass
    await update.message.reply_text("✅ User added.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_rem_user(update, context):
    await update.message.reply_text("🚫 Send User ID to remove:", reply_markup=get_cancel_kb())
    return WAIT_REM_USER
async def handle_rem_user(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    try: execute_query("DELETE FROM users WHERE user_id=?", (int(update.message.text),))
    except: pass
    await update.message.reply_text("✅ User removed.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_add_admin(update, context):
    await update.message.reply_text("👑 Send User ID to make Admin:", reply_markup=get_cancel_kb())
    return WAIT_ADMIN_ID
async def handle_add_admin(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    try: execute_query("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (int(update.message.text),))
    except: pass
    await update.message.reply_text("✅ Admin added.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_rem_admin(update, context):
    await update.message.reply_text("❌ Send Admin ID to remove:", reply_markup=get_cancel_kb())
    return WAIT_REM_ADMIN
async def handle_rem_admin(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    try: execute_query("DELETE FROM admins WHERE user_id=?", (int(update.message.text),))
    except: pass
    await update.message.reply_text("✅ Admin removed.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_broadcast(update, context):
    await update.message.reply_text("📢 Send broadcast message:", reply_markup=get_cancel_kb())
    return WAIT_BROADCAST
async def handle_broadcast(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    users = execute_query("SELECT user_id FROM users", fetch_all=True)
    await update.message.reply_text("⏳ Broadcasting...")
    for u in users:
        try: await context.bot.send_message(chat_id=u['user_id'], text=update.message.text)
        except: pass
    await update.message.reply_text("✅ Announcement sent.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_sup_uname(update, context):
    await update.message.reply_text("✏️ Send new Support Username:", reply_markup=get_cancel_kb())
    return WAIT_SUPPORT_UNAME
async def handle_sup_uname(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('support_username', ?)", (update.message.text,))
    await update.message.reply_text("✅ Username updated.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_sup_link(update, context):
    await update.message.reply_text("🔗 Send new Support Link:", reply_markup=get_cancel_kb())
    return WAIT_SUPPORT_LINK
async def handle_sup_link(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('support_link', ?)", (update.message.text,))
    await update.message.reply_text("✅ Link updated.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

async def prompt_sup_text(update, context):
    await update.message.reply_text("📝 Send new Contact Text:", reply_markup=get_cancel_kb())
    return WAIT_SUPPORT_TEXT
async def handle_sup_text(update, context):
    if await handle_cancel(update, context): return ConversationHandler.END
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('contact_text', ?)", (update.message.text,))
    await update.message.reply_text("✅ Text updated.", reply_markup=get_main_reply_kb(update.effective_user.id))
    return ConversationHandler.END

# --- ASSEMBLE CONVERSATION ---
admin_conv_handler = ConversationHandler(
    entry_points=[
        MessageHandler(filters.Regex('^📦 Add Material$'), prompt_add_mat),
        MessageHandler(filters.Regex('^🗑 Delete Material$'), prompt_del_mat),
        MessageHandler(filters.Regex('^✏️ Edit Material$'), prompt_edit_mat),
        MessageHandler(filters.Regex('^➕ Add Category$'), prompt_add_cat),
        MessageHandler(filters.Regex('^👤 Add User$'), prompt_add_user),
        MessageHandler(filters.Regex('^🚫 Remove User$'), prompt_rem_user),
        MessageHandler(filters.Regex('^👑 Add Admin$'), prompt_add_admin),
        MessageHandler(filters.Regex('^❌ Remove Admin$'), prompt_rem_admin),
        MessageHandler(filters.Regex('^📢 Announcement$'), prompt_broadcast),
        MessageHandler(filters.Regex('^✏️ Edit Username$'), prompt_sup_uname),
        MessageHandler(filters.Regex('^🔗 Edit Link$'), prompt_sup_link),
        MessageHandler(filters.Regex('^📝 Edit Text$'), prompt_sup_text),
    ],
    states={
        WAIT_ADD_MAT_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_add_mat_cat)],
        WAIT_MAT_FILE: [MessageHandler(filters.ALL & ~filters.COMMAND, recv_mat_file)],
        WAIT_MAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_mat_name)],
        WAIT_DEL_MAT_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_del_mat_cat)],
        WAIT_DEL_MAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_del_mat_name)],
        WAIT_DEL_CONFIRM: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_del_confirm)],
        WAIT_EDIT_MAT_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_edit_mat_cat)],
        WAIT_EDIT_MAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_edit_mat_name)],
        WAIT_EDIT_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_edit_action)],
        WAIT_EDIT_NAME_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_edit_name_new)],
        WAIT_EDIT_FILE_NEW: [MessageHandler(filters.ALL & ~filters.COMMAND, recv_edit_file_new)],
        WAIT_EDIT_MOVE_CAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_edit_move_cat)],
        WAIT_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, recv_cat_name)],
        WAIT_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_user)],
        WAIT_REM_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rem_user)],
        WAIT_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_admin)],
        WAIT_REM_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rem_admin)],
        WAIT_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast)],
        WAIT_SUPPORT_UNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sup_uname)],
        WAIT_SUPPORT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sup_link)],
        WAIT_SUPPORT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sup_text)],
    },
    fallbacks=[CommandHandler('cancel', cancel_flow)]
)

from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from telegram import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from utils import is_admin, is_owner, extract_file_info
from database import execute_query
from handlers.keyboards import get_admin_menu_kb
import logging

async def admin_command(update, context):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    kb = get_admin_menu_kb(is_owner(user_id))
    await update.message.reply_text("👑 <b>Admin Panel</b>", parse_mode='HTML', reply_markup=kb)

async def cancel_flow(update, context):
    await update.message.reply_text("❌ Action cancelled. Send /admin to return to the panel.")
    return ConversationHandler.END

# --- ADD MATERIAL FLOW ---
async def prompt_add_mat(update, context):
    query = update.callback_query
    await query.answer()
    cat_id = query.data.split("_")[2]
    context.user_data['temp_cat_id'] = cat_id
    await query.edit_message_text("📤 Please send the File (PDF, ZIP, Video, Photo, Audio), Text, Forwarded Message, or Link for this material.\n\nSend /cancel to abort.")
    return WAIT_MAT_FILE

async def handle_mat_file(update, context):
    file_id, ftype = extract_file_info(update.message)
    if not file_id:
        await update.message.reply_text("❌ Invalid format. Please send a valid document, media, or text.")
        return WAIT_MAT_FILE
    context.user_data['temp_file_id'] = file_id
    context.user_data['temp_file_type'] = ftype
    await update.message.reply_text("📝 Enter Material Name:")
    return WAIT_MAT_NAME

async def handle_mat_name(update, context):
    name = update.message.text
    cat_id = context.user_data.get('temp_cat_id')
    file_id = context.user_data.get('temp_file_id')
    ftype = context.user_data.get('temp_file_type')
    execute_query("INSERT INTO materials (name, category_id, file_id, file_type) VALUES (?, ?, ?, ?)", (name, cat_id, file_id, ftype))
    await update.message.reply_text("✅ Course/Material Added Successfully!\nSend /admin to return.")
    return ConversationHandler.END

# --- ADD CATEGORY FLOW ---
async def prompt_add_cat(update, context):
    await update.callback_query.edit_message_text("📝 Enter new category name (e.g., 🛠 Premium Tools):")
    return WAIT_CAT_NAME

async def handle_cat_name(update, context):
    execute_query("INSERT INTO categories (name) VALUES (?)", (update.message.text,))
    await update.message.reply_text("✅ Category created successfully. /admin to return.")
    return ConversationHandler.END

# --- EDIT MATERIAL FLOW ---
async def prompt_edit_name(update, context):
    context.user_data['edit_mat_id'] = update.callback_query.data.split("_")[2]
    await update.callback_query.edit_message_text("📝 Enter the new name:")
    return WAIT_EDIT_NAME

async def handle_edit_name(update, context):
    mat_id = context.user_data['edit_mat_id']
    execute_query("UPDATE materials SET name=? WHERE id=?", (update.message.text, mat_id))
    await update.message.reply_text("✅ Name updated. /admin to return.")
    return ConversationHandler.END

async def prompt_edit_file(update, context):
    context.user_data['edit_mat_id'] = update.callback_query.data.split("_")[2]
    await update.callback_query.edit_message_text("📤 Send the new file, text, or link to replace the current one:")
    return WAIT_EDIT_FILE

async def handle_edit_file(update, context):
    file_id, ftype = extract_file_info(update.message)
    if not file_id:
        await update.message.reply_text("❌ Invalid format.")
        return WAIT_EDIT_FILE
    mat_id = context.user_data['edit_mat_id']
    execute_query("UPDATE materials SET file_id=?, file_type=? WHERE id=?", (file_id, ftype, mat_id))
    await update.message.reply_text("✅ File replaced successfully. /admin to return.")
    return ConversationHandler.END

# --- USER / ADMIN MANAGEMENT ---
async def prompt_add_user(update, context):
    await update.callback_query.edit_message_text("👤 Send the Telegram User ID to add:")
    return WAIT_USER_ID

async def handle_add_user(update, context):
    try:
        uid = int(update.message.text)
        execute_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (uid,))
        await update.message.reply_text("✅ User added to whitelist. /admin to return.")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Must be numeric.")
    return ConversationHandler.END

async def prompt_rem_user(update, context):
    await update.callback_query.edit_message_text("🚫 Send the Telegram User ID to remove:")
    return WAIT_REM_USER

async def handle_rem_user(update, context):
    try:
        uid = int(update.message.text)
        execute_query("DELETE FROM users WHERE user_id=?", (uid,))
        await update.message.reply_text("✅ User removed from whitelist. /admin to return.")
    except ValueError:
        pass
    return ConversationHandler.END

async def prompt_add_admin(update, context):
    if not is_owner(update.effective_user.id): return ConversationHandler.END
    await update.callback_query.edit_message_text("👑 Send the Telegram User ID to make Admin:")
    return WAIT_ADMIN_ID

async def handle_add_admin(update, context):
    try:
        execute_query("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (int(update.message.text),))
        await update.message.reply_text("✅ Admin added. /admin to return.")
    except ValueError:
        pass
    return ConversationHandler.END

async def prompt_rem_admin(update, context):
    if not is_owner(update.effective_user.id): return ConversationHandler.END
    await update.callback_query.edit_message_text("❌ Send the Telegram Admin ID to remove:")
    return WAIT_REM_ADMIN

async def handle_rem_admin(update, context):
    try:
        execute_query("DELETE FROM admins WHERE user_id=?", (int(update.message.text),))
        await update.message.reply_text("✅ Admin removed. /admin to return.")
    except ValueError:
        pass
    return ConversationHandler.END

# --- BROADCAST ---
async def prompt_broadcast(update, context):
    await update.callback_query.edit_message_text("📢 Send the message you want to broadcast to all approved users:")
    return WAIT_BROADCAST

async def handle_broadcast(update, context):
    msg = update.message.text
    users = execute_query("SELECT user_id FROM users", fetch_all=True)
    sent = 0
    await update.message.reply_text("⏳ Broadcasting...")
    for u in users:
        try:
            await context.bot.send_message(chat_id=u['user_id'], text=msg)
            sent += 1
        except Exception as e:
            pass # Skip users who blocked the bot
    await update.message.reply_text(f"✅ Announcement sent to {sent} users.\n/admin to return.")
    return ConversationHandler.END

# --- SUPPORT SETTINGS ---
async def prompt_sup_uname(update, context):
    await update.callback_query.edit_message_text("✏️ Send the new Support Username (e.g., @Support):")
    return WAIT_SUPPORT_UNAME

async def handle_sup_uname(update, context):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('support_username', ?)", (update.message.text,))
    await update.message.reply_text("✅ Support Username updated. /admin to return.")
    return ConversationHandler.END

async def prompt_sup_link(update, context):
    await update.callback_query.edit_message_text("🔗 Send the new Support Link (e.g., https://t.me/Support):")
    return WAIT_SUPPORT_LINK

async def handle_sup_link(update, context):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('support_link', ?)", (update.message.text,))
    await update.message.reply_text("✅ Support Link updated. /admin to return.")
    return ConversationHandler.END

async def prompt_sup_text(update, context):
    await update.callback_query.edit_message_text("📝 Send the new Contact Text:")
    return WAIT_SUPPORT_TEXT

async def handle_sup_text(update, context):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('contact_text', ?)", (update.message.text,))
    await update.message.reply_text("✅ Contact Text updated. /admin to return.")
    return ConversationHandler.END

# Assemble Conversation Handler for stateful admin flows
admin_conv_handler = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(prompt_add_mat, pattern='^admin_addmat_'),
        CallbackQueryHandler(prompt_add_cat, pattern='^admin_add_category$'),
        CallbackQueryHandler(prompt_add_user, pattern='^admin_add_user$'),
        CallbackQueryHandler(prompt_rem_user, pattern='^admin_rem_user$'),
        CallbackQueryHandler(prompt_add_admin, pattern='^admin_add_admin$'),
        CallbackQueryHandler(prompt_rem_admin, pattern='^admin_rem_admin$'),
        CallbackQueryHandler(prompt_broadcast, pattern='^admin_broadcast$'),
        CallbackQueryHandler(prompt_sup_uname, pattern='^admin_sup_uname$'),
        CallbackQueryHandler(prompt_sup_link, pattern='^admin_sup_link$'),
        CallbackQueryHandler(prompt_sup_text, pattern='^admin_sup_text$'),
        CallbackQueryHandler(prompt_edit_name, pattern='^admin_editname_'),
        CallbackQueryHandler(prompt_edit_file, pattern='^admin_editfile_'),
    ],
    states={
        WAIT_MAT_FILE: [MessageHandler(filters.ALL & ~filters.COMMAND, handle_mat_file)],
        WAIT_MAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_mat_name)],
        WAIT_CAT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cat_name)],
        WAIT_USER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_user)],
        WAIT_REM_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rem_user)],
        WAIT_ADMIN_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_add_admin)],
        WAIT_REM_ADMIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rem_admin)],
        WAIT_BROADCAST: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_broadcast)],
        WAIT_SUPPORT_UNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sup_uname)],
        WAIT_SUPPORT_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sup_link)],
        WAIT_SUPPORT_TEXT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_sup_text)],
        WAIT_EDIT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_edit_name)],
        WAIT_EDIT_FILE: [MessageHandler(filters.ALL & ~filters.COMMAND, handle_edit_file)],
    },
    fallbacks=[CommandHandler('cancel', cancel_flow)]
)
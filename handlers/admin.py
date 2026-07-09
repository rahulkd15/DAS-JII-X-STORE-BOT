from telegram.ext import ConversationHandler, CallbackQueryHandler, MessageHandler, filters, CommandHandler
from config import *
from utils import is_owner, extract_file_info
from database import execute_query

async def admin_command(update, context):
    pass # Command ki ab zarurat nahi kyunki button aagaya

async def cancel_flow(update, context):
    await update.message.reply_text("❌ Action cancelled.")
    return ConversationHandler.END

# --- MAT / CAT / SUPPORT FLOWS (In-line ke through) ---
async def prompt_add_mat(update, context):
    query = update.callback_query
    await query.answer()
    context.user_data['temp_cat_id'] = query.data.split("_")[2]
    await query.edit_message_text("📤 Send the File, Text, Forwarded Message, or Link.\nSend /cancel to abort.")
    return WAIT_MAT_FILE

async def handle_mat_file(update, context):
    file_id, ftype = extract_file_info(update.message)
    if not file_id:
        await update.message.reply_text("❌ Invalid format.")
        return WAIT_MAT_FILE
    context.user_data['temp_file_id'] = file_id
    context.user_data['temp_file_type'] = ftype
    await update.message.reply_text("📝 Enter Material Name:")
    return WAIT_MAT_NAME

async def handle_mat_name(update, context):
    name, cat_id, file_id, ftype = update.message.text, context.user_data.get('temp_cat_id'), context.user_data.get('temp_file_id'), context.user_data.get('temp_file_type')
    execute_query("INSERT INTO materials (name, category_id, file_id, file_type) VALUES (?, ?, ?, ?)", (name, cat_id, file_id, ftype))
    await update.message.reply_text("✅ Material Added Successfully!")
    return ConversationHandler.END

async def prompt_add_cat(update, context):
    await update.callback_query.edit_message_text("📝 Enter new category name (e.g., 🛠 Premium Tools):")
    return WAIT_CAT_NAME

async def handle_cat_name(update, context):
    execute_query("INSERT INTO categories (name) VALUES (?)", (update.message.text,))
    await update.message.reply_text("✅ Category created successfully.")
    return ConversationHandler.END

async def prompt_edit_name(update, context):
    context.user_data['edit_mat_id'] = update.callback_query.data.split("_")[2]
    await update.callback_query.edit_message_text("📝 Enter the new name:")
    return WAIT_EDIT_NAME

async def handle_edit_name(update, context):
    execute_query("UPDATE materials SET name=? WHERE id=?", (update.message.text, context.user_data['edit_mat_id']))
    await update.message.reply_text("✅ Name updated.")
    return ConversationHandler.END

async def prompt_edit_file(update, context):
    context.user_data['edit_mat_id'] = update.callback_query.data.split("_")[2]
    await update.callback_query.edit_message_text("📤 Send the new file, text, or link:")
    return WAIT_EDIT_FILE

async def handle_edit_file(update, context):
    file_id, ftype = extract_file_info(update.message)
    if not file_id: return WAIT_EDIT_FILE
    execute_query("UPDATE materials SET file_id=?, file_type=? WHERE id=?", (file_id, ftype, context.user_data['edit_mat_id']))
    await update.message.reply_text("✅ File replaced.")
    return ConversationHandler.END

async def prompt_sup_uname(update, context):
    await update.callback_query.edit_message_text("✏️ Send the new Support Username:")
    return WAIT_SUPPORT_UNAME

async def handle_sup_uname(update, context):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('support_username', ?)", (update.message.text,))
    await update.message.reply_text("✅ Support Username updated.")
    return ConversationHandler.END

async def prompt_sup_link(update, context):
    await update.callback_query.edit_message_text("🔗 Send the new Support Link:")
    return WAIT_SUPPORT_LINK

async def handle_sup_link(update, context):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('support_link', ?)", (update.message.text,))
    await update.message.reply_text("✅ Support Link updated.")
    return ConversationHandler.END

async def prompt_sup_text(update, context):
    await update.callback_query.edit_message_text("📝 Send the new Contact Text:")
    return WAIT_SUPPORT_TEXT

async def handle_sup_text(update, context):
    execute_query("INSERT OR REPLACE INTO settings (key, value) VALUES ('contact_text', ?)", (update.message.text,))
    await update.message.reply_text("✅ Contact Text updated.")
    return ConversationHandler.END

# --- BOTTOM KEYBOARD FLOWS (Naye Text Buttons ke through) ---
async def prompt_add_user(update, context):
    await update.message.reply_text("👤 Send the Telegram User ID to add:\nSend /cancel to abort.")
    return WAIT_USER_ID

async def handle_add_user(update, context):
    try:
        execute_query("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (int(update.message.text),))
        await update.message.reply_text("✅ User added to whitelist.")
    except ValueError:
        await update.message.reply_text("❌ Invalid ID.")
    return ConversationHandler.END

async def prompt_rem_user(update, context):
    await update.message.reply_text("🚫 Send the Telegram User ID to remove:\nSend /cancel to abort.")
    return WAIT_REM_USER

async def handle_rem_user(update, context):
    try:
        execute_query("DELETE FROM users WHERE user_id=?", (int(update.message.text),))
        await update.message.reply_text("✅ User removed from whitelist.")
    except ValueError: pass
    return ConversationHandler.END

async def prompt_add_admin(update, context):
    if not is_owner(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("👑 Send the Telegram User ID to make Admin:\nSend /cancel to abort.")
    return WAIT_ADMIN_ID

async def handle_add_admin(update, context):
    try:
        execute_query("INSERT OR IGNORE INTO admins (user_id) VALUES (?)", (int(update.message.text),))
        await update.message.reply_text("✅ Admin added.")
    except ValueError: pass
    return ConversationHandler.END

async def prompt_rem_admin(update, context):
    if not is_owner(update.effective_user.id): return ConversationHandler.END
    await update.message.reply_text("❌ Send the Telegram Admin ID to remove:\nSend /cancel to abort.")
    return WAIT_REM_ADMIN

async def handle_rem_admin(update, context):
    try:
        execute_query("DELETE FROM admins WHERE user_id=?", (int(update.message.text),))
        await update.message.reply_text("✅ Admin removed.")
    except ValueError: pass
    return ConversationHandler.END

async def prompt_broadcast(update, context):
    await update.message.reply_text("📢 Send the broadcast message:\nSend /cancel to abort.")
    return WAIT_BROADCAST

async def handle_broadcast(update, context):
    users = execute_query("SELECT user_id FROM users", fetch_all=True)
    sent = 0
    await update.message.reply_text("⏳ Broadcasting...")
    for u in users:
        try:
            await context.bot.send_message(chat_id=u['user_id'], text=update.message.text)
            sent += 1
        except Exception: pass
    await update.message.reply_text(f"✅ Announcement sent to {sent} users.")
    return ConversationHandler.END

# --- ASSEMBLE CONVERSATION ---
admin_conv_handler = ConversationHandler(
    entry_points=[
        # Text based inputs from Reply Keyboard
        MessageHandler(filters.Regex('^👤 Add User$'), prompt_add_user),
        MessageHandler(filters.Regex('^🚫 Remove User$'), prompt_rem_user),
        MessageHandler(filters.Regex('^👑 Add Admin$'), prompt_add_admin),
        MessageHandler(filters.Regex('^❌ Remove Admin$'), prompt_rem_admin),
        MessageHandler(filters.Regex('^📢 Announcement$'), prompt_broadcast),
        
        # Inline Button based inputs
        CallbackQueryHandler(prompt_add_mat, pattern='^admin_addmat_'),
        CallbackQueryHandler(prompt_add_cat, pattern='^admin_add_category$'),
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

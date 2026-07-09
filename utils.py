from database import execute_query
from config import OWNER_ID
import html

def is_owner(user_id):
    # Ye line tujhe 100% owner bana degi
    return str(user_id) == str(OWNER_ID)

def is_admin(user_id):
    if is_owner(user_id):
        return True
    admin = execute_query("SELECT user_id FROM admins WHERE user_id=?", (user_id,), fetch=True)
    return bool(admin)

def is_approved(user_id):
    if is_admin(user_id):
        return True
    user = execute_query("SELECT user_id FROM users WHERE user_id=?", (user_id,), fetch=True)
    return bool(user)

def extract_file_info(message):
    if message.document:
        return message.document.file_id, "document"
    elif message.video:
        return message.video.file_id, "video"
    elif message.audio:
        return message.audio.file_id, "audio"
    elif message.photo:
        return message.photo[-1].file_id, "photo"
    elif message.text:
        return message.text, "text"
    else:
        return None, None

def escape_html(text):
    return html.escape(str(text))

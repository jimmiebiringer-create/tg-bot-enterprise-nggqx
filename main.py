import os
import json
import asyncio
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from pyrogram import Client

# إعداد السجل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 1. إعدادات بوت التوكن
TOKEN = "8817693483:AAGTiSzJUkkYrT62EBzgsBimwHLVDd_CrGs"
OWNER_ID = 1443724632

# 2. إعدادات اليوزر بوت
API_ID = int(os.getenv("API_ID", "36304618"))
API_HASH = "aba393ee19abc3e6afe1d7e6e233e9a9"
SESSION_STRING = "AgIp9uoAfGToEx2K-rUaaL12gbc0Ykk00z09-kC5SQ_H2QUkhQJm1eRrbb0uz2rgr34GyIDmujtk83Rll6IHOtNIZwyTd5uxsjf-JyzLSbggo6FJCc75u440tDZs5dE2uWQxmnSJbu6LvJkZwvQY2poSmlFcpz6NuRT4mA2wF7Yb4LxSv1rB937WwvPsH82J2ZrAAmrCyzo86iYxmpuZcJ3-pz9COOUH8zMtVP3M-x-pc_YxQciferBYXml2NxrwRV_J6msf77p3sKo1pdjn0XdpAjdH94YND0uAKW-ICg2OcC7r5Ebss4SBwUmQj-8Hx-cakY9Tpx18qaXBvwyLDKCQkhTPwAAAAAGMZxrBAA"

userbot = Client(
    "my_userbot_session",
    session_string=SESSION_STRING,
    api_id=API_ID,
    api_hash=API_HASH
)

USERS_FILE = "users.json"
BANNED_FILE = "banned.json"

def load_data():
    users = {}
    banned = set()
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                users = {int(k) if str(k).isdigit() or (str(k).startswith("-") and str(k)[1:].isdigit()) else k: v for k, v in data.items()}
        except Exception:
            pass
            
    if os.path.exists(BANNED_FILE):
        try:
            with open(BANNED_FILE, "r", encoding="utf-8") as f:
                banned_list = json.load(f)
                banned = {int(x) if str(x).isdigit() or (str(x).startswith("-") and str(x)[1:].isdigit()) else x for x in banned_list}
        except Exception:
            pass
            
    return users, banned

def save_data():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(all_users, f, ensure_ascii=False, indent=4)
        with open(BANNED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(banned_users), f, ensure_ascii=False, indent=4)
    except Exception:
        pass

all_users, banned_users = load_data()

waiting_for_gif = set()
global_welcome_gif = None
waiting_for_id_extraction = set()
waiting_for_ban = set()
waiting_for_unban = set()
waiting_for_broadcast = set()

def with_retry(retries=3, delay=1.5):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for attempt in range(1, retries + 1):
                try:
                    async with userbot:
                        return await func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries:
                        raise e
                    await asyncio.sleep(delay)
        return wrapper
    return decorator

def get_owner_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("ID Extraction"), KeyboardButton("Select GIF")],
        [KeyboardButton("Number of users"), KeyboardButton("Ban User"), KeyboardButton("Unban User")],
        [KeyboardButton("Broadcast")]
    ], resize_keyboard=True)

def get_user_keyboard():
    return ReplyKeyboardMarkup([[KeyboardButton("ID Extraction")]], resize_keyboard=True)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    if user_id in banned_users:
        return

    name = user.first_name or "بدون اسم"
    username = f"@{user.username}" if user.username else "لا يوجد"
    
    if user_id not in all_users:
        all_users[user_id] = {"name": name, "username": username, "id": user_id}
        save_data()

    reply_markup = get_owner_keyboard() if user_id == OWNER_ID else get_user_keyboard()
    caption_text = "تمت برمجة البوت بواسطة #حربي"

    if global_welcome_gif:
        try:
            await update.message.reply_animation(animation=global_welcome_gif, caption=caption_text, reply_markup=reply_markup)
            return
        except Exception:
            pass

    await update.message.reply_text(f"🤖 مرحباً بك في لوحة التحكم!\n\n{caption_text}", reply_markup=reply_markup)

async def clear_owner_states(user_id):
    for s in [waiting_for_gif, waiting_for_id_extraction, waiting_for_ban, waiting_for_unban, waiting_for_broadcast]:
        if user_id in s:
            s.remove(user_id)

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waiting_for_gif, global_welcome_gif, waiting_for_id_extraction, waiting_for_ban, waiting_for_unban, waiting_for_broadcast
    user = update.message.from_user
    user_id = user.id
    text = update.message.text
    animation = update.message.animation

    if user_id in banned_users:
        return

    if user_id == OWNER_ID and user_id in waiting_for_broadcast:
        waiting_for_broadcast.remove(user_id)
        success_count, fail_count = 0, 0
        status_msg = await update.message.reply_text("⏳ جاري إرسال الإذاعة لجميع المستخدمين...")
        for target_id in list(all_users.keys()):
            if target_id == OWNER_ID:
                continue
            try:
                await context.bot.copy_message(chat_id=target_id, from_chat_id=update.message.chat_id, message_id=update.message.message_id)
                success_count += 1
                await asyncio.sleep(0.05)
            except Exception:
                fail_count += 1
        await status_msg.edit_text(f"✅ تم إرسال الإذاعة بنجاح.\n- وصل إلى: {success_count}\n- فشل الوصول إلى: {fail_count}")
        return

    if animation and user_id == OWNER_ID and user_id in waiting_for_gif:
        waiting_for_gif.remove(user_id)
        global_welcome_gif = animation.file_id
        await update.message.reply_animation(animation=animation.file_id, caption="تم تحديث وتثبيت الـ GIF للترحيب بنجاح بواسطة #حربي", reply_markup=get_owner_keyboard())
        return

    if text == "ID Extraction":
        await clear_owner_states(user_id)
        waiting_for_id_extraction.add(user_id)
        await update.message.reply_text("Send ID, USER (@USERNAME), or Link:")
        
    elif text == "Select GIF" and user_id == OWNER_ID:
        await clear_owner_states(user_id)
        waiting_for_gif.add(user_id)
        await update.message.reply_text("Send GIF")

    elif text == "Number of users" and user_id == OWNER_ID:
        await clear_owner_states(user_id)
        count = len(all_users)
        users_list_text = f"📊 **Number of users:** {count}\n\n"
        for u in all_users.values():
            users_list_text += f"NAME: {u['name']}\nID: {u['id']}\nUSER: {u['username']}\n-------------------\n"
        if len(users_list_text) > 4096:
            for x in range(0, len(users_list_text), 4096):
                await update.message.reply_text(users_list_text[x:x+4096])
        else:
            await update.message.reply_text(users_list_text)

    elif text == "Ban User" and user_id == OWNER_ID:
        await clear_owner_states(user_id)
        waiting_for_ban.add(user_id)
        await update.message.reply_text("Send ID or USER to BAN:")

    elif text == "Unban User" and user_id == OWNER_ID:
        await clear_owner_states(user_id)
        waiting_for_unban.add(user_id)
        await update.message.reply_text("Send ID or USER to UNBAN:")

    elif text == "Broadcast" and user_id == OWNER_ID:
        await clear_owner_states(user_id)
        waiting_for_broadcast.add(user_id)
        await update.message.reply_text("📢 قم بإرسال الرسالة ليتم إذاعتها لجميع المستخدمين:")

    # معالجة استخراج المعرفات واليوزرات والروابط
    elif text and user_id in waiting_for_id_extraction:
        raw_query = text.strip()
        waiting_for_id_extraction.remove(user_id)
        
        query = raw_query
        if "t.me/" in query:
            query = query.split("t.me/")[-1].split("?")[0].strip("/")
        if query.startswith("@"):
            query = query[1:]
            
        msg = await update.message.reply_text("Work in progress⌛")
        target_user = None
        
        @with_retry(retries=3, delay=1.5)
        async def fetch_target():
            nonlocal target_user
            if query.isdigit() or (query.startswith("-") and query[1:].isdigit()):
                try:
                    target_user = await userbot.get_users(int(query))
                except:
                    pass
            
            if not target_user:
                try:
                    target_user = await userbot.get_users(query)
                except:
                    pass
            
            if not target_user:
                try:
                    target_user = await userbot.get_chat(query)
                except:
                    pass

        try:
            await fetch_target()

            if not target_user:
                await msg.edit_text("❌Error")
                return

            name = getattr(target_user, "first_name", None) or getattr(target_user, "title", "بدون اسم")
            last_name = getattr(target_user, "last_name", None)
            if last_name:
                name += f" {last_name}"
                
            uid = target_user.id
            raw_username = getattr(target_user, "username", None)
            username = f"@{raw_username}" if raw_username else "لا يوجد يوزر"
            
            response_text = (
                f"NAME: {name}\n"
                f"ID: {uid}\n"
                f"USER: {username}"
            )
            await msg.edit_text(response_text)
            
        except Exception:
            await msg.edit_text("❌Error")

    elif text and user_id in waiting_for_ban and user_id == OWNER_ID:
        target = text.strip()
        waiting_for_ban.remove(user_id)
        banned_users.add(int(target) if target.isdigit() or (target.startswith("-") and target[1:].isdigit()) else target.lower())
        save_data()
        await update.message.reply_text(f"✅ User ({target}) has been banned successfully.")

    elif text and user_id in waiting_for_unban and user_id == OWNER_ID:
        target = text.strip()
        waiting_for_unban.remove(user_id)
        target_check = int(target) if target.isdigit() or (target.startswith("-") and target[1:].isdigit()) else target.lower()
        if target_check in banned_users:
            banned_users.remove(target_check)
            save_data()
            await update.message.reply_text(f"✅ User ({target}) has been unbanned successfully.")
        else:
            await update.message.reply_text(f"⚠️ User ({target}) is not in the ban list.")

def main():
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(MessageHandler((filters.ALL & ~filters.COMMAND), handle_messages))
    print("🤖 البوت يعمل بكامل التدعيمات وبدون أخطاء...")
    application.run_polling()

if __name__ == "__main__":
    main()

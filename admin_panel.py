from pyrogram import Client, filters
from pymongo import MongoClient
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Load env
import os
from dotenv import load_dotenv
load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MONGO_URI = os.getenv("MONGO_URI")
db = MongoClient(MONGO_URI).referral_bot
settings = db.settings

# Default settings if not exist
if settings.count_documents({}) == 0:
    settings.insert_one({
        "referral_reward": 4,
        "signup_bonus": 0,
        "min_withdraw": 30,
        "force_join": ["@JVTalk"]
    })

def get_settings():
    return settings.find_one()

def update_setting(field, value):
    settings.update_one({}, {"$set": {field: value}})

def admin_only(func):
    async def wrapper(client, message):
        if message.from_user.id != ADMIN_ID:
            return
        await func(client, message)
    return wrapper

@Client.on_message(filters.command("admin"))
@admin_only
async def admin_menu(client, message):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Force‑Join", callback_data="ctl_force")],
        [InlineKeyboardButton("💰 Referral ₹", callback_data="ctl_ref")],
        [InlineKeyboardButton("🎁 Signup Bonus", callback_data="ctl_bonus")],
        [InlineKeyboardButton("🔽 Min Withdraw", callback_data="ctl_minwit")],
    ])
    await message.reply("👑 Admin Panel:", reply_markup=kb)

@Client.on_callback_query()
@admin_only
async def callbacks(client, cq):
    mer = get_settings()
    data = cq.data
    if data == "ctl_force":
        text = "📢 Current force-join channels:\n" + "\n".join(mer["force_join"])
        text += "\n\nSend 'add @channel' or 'del @channel'"
        await cq.message.edit(text)
    elif data == "ctl_ref":
        await cq.message.edit(f"💰 Referral Reward: ₹{mer['referral_reward']}\nSend new value.")
    elif data == "ctl_bonus":
        await cq.message.edit(f"🎁 Signup Bonus: ₹{mer['signup_bonus']}\nSend new value.")
    elif data == "ctl_minwit":
        await cq.message.edit(f"🔽 Min Withdraw: ₹{mer['min_withdraw']}\nSend new value.")
    await cq.answer()

@Client.on_message(filters.private & filters.user(ADMIN_ID))
async def admin_setters(client, message):
    mer = get_settings()
    txt = message.text.strip().split()
    if txt[0].lower() == "add" and txt[1].startswith("@"):
        ch = txt[1]
        if ch not in mer["force_join"]:
            mer["force_join"].append(ch)
            update_setting("force_join", mer["force_join"])
            await message.reply(f"Added {ch}")
    elif txt[0].lower() == "del" and txt[1].startswith("@"):
        ch = txt[1]
        if ch in mer["force_join"]:
            mer["force_join"].remove(ch)
            update_setting("force_join", mer["force_join"])
            await message.reply(f"Removed {ch}")
    elif txt[0].isdigit():
        val = int(txt[0])
        if "ref" in message.reply_to_message.text.lower():
            update_setting("referral_reward", val)
            await message.reply(f"Referral reward updated to ₹{val}")
        elif "bonus" in message.reply_to_message.text.lower():
            update_setting("signup_bonus", val)
            await message.reply(f"Signup bonus updated to ₹{val}")
        elif "withdraw" in message.reply_to_message.text.lower():
            update_setting("min_withdraw", val)
            await message.reply(f"Min withdraw updated to ₹{val}")

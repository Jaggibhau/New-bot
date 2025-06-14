from pyrogram import Client, filters
from pymongo import MongoClient
import os
from admin_panel import get_settings
from keep_alive import keep_alive
from pyrogram.errors import UserNotParticipant
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
MONGO_URI = os.getenv("MONGO_URI")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

db = MongoClient(MONGO_URI).referral_bot
users = db.users

app = Client("bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
keep_alive()

def check_force_join(func):
    async def wrapper(client, message):
        mer = get_settings()
        for ch in mer["force_join"]:
            try:
                mem = await client.get_chat_member(ch, message.from_user.id)
                if mem.status in ["left", "kicked"]:
                    raise UserNotParticipant
            except UserNotParticipant:
                return await message.reply(
                    f"🚫 Please join {ch} to use this bot.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Join Here", url=f"https://t.me/{ch.strip('@')}")]])
                )
        return await func(client, message)
    return wrapper

@app.on_message(filters.command("start"))
@check_force_join
async def start(_, msg):
    mer = get_settings()
    uid = msg.from_user.id
    parts = msg.text.split()
    ref = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else None

    user = users.find_one({"_id": uid})
    if not user:
        bal = mer["signup_bonus"]
        users.insert_one({"_id": uid, "ref": ref, "balance": bal})
        if ref:
            users.update_one({"_id": ref}, {"$inc": {"balance": mer["referral_reward"]}})
        await msg.reply(f"Welcome! Your balance: ₹{bal}")
    else:
        await msg.reply("Welcome back!")

@app.on_message(filters.command("refer"))
@check_force_join
async def refer(_, msg):
    await msg.reply(f"Share this link:\nhttps://t.me/{(await app.get_me()).username}?start={msg.from_user.id}")

@app.on_message(filters.command("balance"))
@check_force_join
async def bal(_, msg):
    u = users.find_one({"_id": msg.from_user.id})
    await msg.reply(f"Your balance: ₹{u['balance']}")

@app.on_message(filters.command("withdraw"))
@check_force_join
async def withdraw(_, msg):
    mer = get_settings()
    u = users.find_one({"_id": msg.from_user.id})
    if u["balance"] < mer["min_withdraw"]:
        return await msg.reply(f"Need at least ₹{mer['min_withdraw']} to withdraw.")
    users.update_one({"_id": msg.from_user.id}, {"$set": {"balance": 0}})
    await msg.reply("✅ Withdraw request sent!")
    await app.send_message(ADMIN_ID, f"User @{msg.from_user.username} requested withdrawal of ₹{u['balance']}")

# Optional: more commands like /help or /stats for admin

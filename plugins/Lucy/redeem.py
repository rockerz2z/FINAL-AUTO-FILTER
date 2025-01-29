import string
import random
from datetime import datetime, timedelta
import pytz
from pyrogram import Client, filters
from info import ADMINS, LOG_CHANNEL
from utils import get_seconds  # Assuming get_seconds function is defined in utils module
from database.users_chats_db import db  # Assuming db functions are defined in users_chats_db module
from pyrogram.errors import MessageTooLong
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Example in-memory storage for redeem codes and redeemed users
VALID_REDEEM_CODES = {}
REDEEMED_USERS = {}  # Dictionary to store redeemed users and their expiry times


# Function to generate a redeem code
def generate_code(length=12):
    letters_and_digits = string.ascii_uppercase + string.digits  # Use only uppercase letters and digits
    random_string = ''.join(random.choice(letters_and_digits) for _ in range(length))
    return f"LUCY{random_string}"

@Client.on_message(filters.command("add_redeem") & filters.user(ADMINS))
async def add_redeem_code(client, message):
    if len(message.command) == 2:
        time = message.command[1]
        code = generate_code()
        VALID_REDEEM_CODES[code] = time

        await message.reply_text(
            f"➩Redeem code added successfully!\n➩Code: '<code>{code}</code>'\n➩Duration: {time}",
            disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            "<b>♻Usage:\n\n➩ <code>/add_redeem 1min</code>,\n➩ <code>/add_redeem 1hour</code>,\n➩ <code>/add_redeem 1day</code>,\n➩ <code>/add_redeem 1month</code>,\n➩ <code>/add_redeem 1year</code></b>",
            disable_web_page_preview=True
        )

@Client.on_message(filters.regex(r"LUCY[A-Z0-9]{12}"))  # Detect messages containing redeem codes
async def redeem_code(client, message):
    redeem_code = message.text.strip()

    if redeem_code in VALID_REDEEM_CODES:
        try:
            time = VALID_REDEEM_CODES.pop(redeem_code)  # Remove redeem code after use
            user_id = message.from_user.id
            user = await client.get_users(user_id)
            seconds = await get_seconds(time)

            if seconds > 0:
                expiry_time = datetime.now() + timedelta(seconds=seconds)
                user_data = {"id": user_id, "expiry_time": expiry_time}
                await db.update_user(user_data)

                # Retrieve user and expiry time for confirmation message
                data = await db.get_user(user_id)
                expiry = data.get("expiry_time")
                expiry_str_in_ist = expiry.astimezone(pytz.timezone("Asia/Kolkata")).strftime("%d-%m-%Y\n⏱️ ᴇxᴘɪʀʏ ᴛɪᴍᴇ : %I:%M:%S %p")

                # Store redeemed user information
                REDEEMED_USERS[user_id] = {
                    "user": user,
                    "time": time,
                    "expiry_time": expiry_str_in_ist
                }

                await message.reply_text(
                    f"Premium activated successfully!\n\nUser: {user.mention}\nUser ID: {user_id}\nPremium Access: {time}\n\nExpiry Date: {expiry_str_in_ist}",
                    disable_web_page_preview=True
                )

                await client.send_message(
                    chat_id=user_id,
                    text=f"👋 ʜᴇʏ {user.mention},\nᴛʜᴀɴᴋ ʏᴏᴜ ꜰᴏʀ ᴘᴜʀᴄʜᴀꜱɪɴɢ ᴘʀᴇᴍɪᴜᴍ.\nᴇɴᴊᴏʏ !! ✨🎉\n\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n⏳ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}",
                    disable_web_page_preview=True
                )

                await client.send_message(
                    LOG_CHANNEL,
                    text=f"#Redeem_Premium\n\n👤 ᴜꜱᴇʀ : {user.mention}\n⚡ ᴜꜱᴇʀ ɪᴅ : <code>{user_id}</code>\n⏰ ᴘʀᴇᴍɪᴜᴍ ᴀᴄᴄᴇꜱꜱ : <code>{time}</code>\n⌛️ ᴇxᴘɪʀʏ ᴅᴀᴛᴇ : {expiry_str_in_ist}",
                    disable_web_page_preview=True
                )

            else:
                await message.reply_text("Invalid time format in redeem code.")

        except Exception as e:
            print(f"Error redeeming code: {str(e)}")
            await message.reply_text("An error occurred while redeeming the code. Please try again later.")

    else:
        await message.reply_text("Invalid Redeem Code or Expired.")

@Client.on_message(filters.command("redeemusers") & filters.user(ADMINS))
async def redeem_users_list(client, message):
    if REDEEMED_USERS:
        text = "<b>List of Redeemed Users:</b>\n\n"
        for user_id, data in REDEEMED_USERS.items():
            user = data["user"]
            time = data["time"]
            expiry_time = data["expiry_time"]
            text += f"👤 User: {user.mention}\n🔹 User ID: <code>{user_id}</code>\n🔸 Premium Access: <code>{time}</code>\n⌛ Expiry Date: {expiry_time}\n\n"
        
        await message.reply_text(text, disable_web_page_preview=True)
    else:
        await message.reply_text("No users have redeemed any codes yet.")

async def get_seconds(time_str):
    time_mapping = {
        'min': 60,
        'hour': 3600,
        'day': 86400,
        'month': 2592000,  # Assuming 30 days for simplicity
        'year': 31536000
    }

    for unit in time_mapping:
        if time_str.endswith(unit):
            value = int(time_str.replace(unit, '').strip())
            return value * time_mapping[unit]
    
    return 0  # Return 0 if format is incorrect

# Define the command handler for /redeem
@Client.on_message(filters.command("redeem") & filters.private)
async def redeem_premium(client, message):
    # Create an inline button that triggers the "seeplans" callback
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🌟 Buy Premium", callback_data="seeplans")
            ]
        ]
    )

    # Send the message to the user with the inline button
    await message.reply_text(
        "**🎁 Kindly provide the redeem code for premium activation.\n\n"
        "If you don't have a redeem code, you can purchase one here.**",
        reply_markup=keyboard
    )

@Client.on_message(filters.command("redeem_20") & filters.user(ADMINS))
async def redeem_20_codes(client, message):
    if len(message.command) == 2:
        time = message.command[1]
        codes_list = []

        for _ in range(20):
            code = generate_code()
            VALID_REDEEM_CODES[code] = time
            codes_list.append(code)

        # Creating the formatted response with each redeem code
        codes_message = "\n".join([f"➔ <code>{code}</code>" for code in codes_list])

        # Inline button with the redeem link
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("• ʀᴇᴅᴇᴇᴍ ʜᴇʀᴇ •", url="https://t.me/Lucy_Filter_bot")]]
        )

        # Final message format
        await message.reply_text(
            f"Gɪғᴛᴄᴏᴅᴇ Gᴇɴᴇʀᴀᴛᴇᴅ ✅\nAᴍᴏᴜɴᴛ: 20\n\n{codes_message}\n\nᴅᴜʀᴀᴛɪᴏɴ : {time}\n\n"
            "𝗥𝗲𝗱𝗲𝗲𝗺 𝗜𝗻𝘀𝘁𝗿𝘂𝗰𝘁𝗶𝗼𝗻\n"
            "ᴊᴜsᴛ ᴄʟɪᴄᴋ ᴄᴏᴅᴇ ᴛᴏ ᴄᴏᴘʏ ɪᴛ ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ "
            "@lucy_filter_bot",
            reply_markup=keyboard,
            disable_web_page_preview=True
        )
    else:
        await message.reply_text(
            "<b>♻Usage:\n\n➩ <code>/redeem_20 1min</code>,\n➩ <code>/redeem_20 1hour</code>,\n➩ <code>/redeem_20 1day</code>,\n➩ <code>/redeem_20 1month</code>,\n➩ <code>/redeem_20 1year</code></b>",
            disable_web_page_preview=True
        )

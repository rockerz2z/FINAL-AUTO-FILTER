import os
import logging
import random
import asyncio
from gtts import gTTS
from langdetect import detect
from pyrogram import Client as app, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction
from lexica import *

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store user chat history (Limited to last 5 messages per user)
user_history = {}

# Function to extract content safely
def extract_content(response):
    if isinstance(response, dict) and 'content' in response:
        return response['content']
    elif isinstance(response, list):
        return "\n".join(item['text'] for item in response if isinstance(item, dict) and 'text' in item)
    return "No response received."

# Function to split text for gTTS
def split_text(text, max_length=200):
    words = text.split()
    chunks, current_chunk = [], ""

    for word in words:
        if len(current_chunk) + len(word) + 1 > max_length:
            chunks.append(current_chunk)
            current_chunk = word
        else:
            current_chunk += " " + word
    chunks.append(current_chunk)
    return chunks

# Function to detect language for TTS
def detect_language(text):
    try:
        return detect(text)
    except:
        return "en"  # Default to English

# Universal AI Chat Handler with history support
async def handle_ai_query(client: Client, message: Message, action: ChatAction, reply_with_voice=False):
    try:
        await client.send_chat_action(message.chat.id, action)
        name = message.from_user.first_name or "User"

        query = message.text.strip().split(maxsplit=1)
        if len(query) < 2:
            await message.reply_text(f"<b>Hello {name}, how can I assist you today?</b>", parse_mode="html")
            return

        user_id = message.from_user.id
        query = query[1]

        # Store user chat history (limit to last 5 messages)
        if user_id not in user_history:
            user_history[user_id] = []
        if len(user_history[user_id]) >= 5:
            user_history[user_id].pop(0)  # Remove oldest message
        user_history[user_id].append({"role": "user", "content": query})

        messages = user_history[user_id]

        lexica_client = AsyncClient()
        try:
            response = await lexica_client.ChatCompletion(
                {"messages": messages, "model": languageModels.gpt}
            )
            content = extract_content(response)

            # Simulate AI typing delay (random between 1.5s - 3s)
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            await asyncio.sleep(random.uniform(1.5, 3))

            if not content.strip():
                content = "⚠️ AI did not return a response. Try again."

            if reply_with_voice:
                content_chunks = split_text(content)
                for i, chunk in enumerate(content_chunks):
                    lang = detect_language(chunk)  # Auto-detect language
                    audio_file = f"response_{i}.mp3"
                    tts = gTTS(text=chunk, lang=lang)
                    tts.save(audio_file)

                    await client.send_voice(chat_id=message.chat.id, voice=audio_file)
                    os.remove(audio_file)  # Clean up after sending
            else:
                await message.reply_text(f"<b>🤖 AI:</b>\n{content}", parse_mode="html")
        finally:
            await lexica_client.close()

    except Exception as e:
        logger.error(f"Error in AI handler: {str(e)}")
        await message.reply_text("⚠️ Oops! Something went wrong. Please try again later.")

# Lucy AI Command
@app.on_message(filters.command(["ucy"], prefixes=["L", "i"]))
async def gpt_handler(client: Client, message: Message):
    await handle_ai_query(client, message, ChatAction.TYPING, reply_with_voice=False)

# General AI Chat Command
@app.on_message(filters.command(["gpt", "ai", "ask", "Master"], prefixes=["+", ".", "/", "-", "?", "$", "#", "&"]))
async def chat_gpt(client: Client, message: Message):
    await handle_ai_query(client, message, ChatAction.TYPING, reply_with_voice=False)

# Voice Assistant Command
@app.on_message(filters.command(["ssis"], prefixes=["a", "A"]))
async def chat_annie(client: Client, message: Message):
    await handle_ai_query(client, message, ChatAction.RECORD_AUDIO, reply_with_voice=True)

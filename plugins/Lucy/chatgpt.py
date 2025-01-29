import os
from gtts import gTTS

from pyrogram import Client as pbot, filters
from pyrogram.types import Message
from pyrogram.enums import ChatAction

from lexica import *

def extract_content(response):
    if isinstance(response, dict):
        return response.get('content', 'No content available.')
    return str(response)

@pbot.on_message(filters.command(["ucy"], prefixes=["l", "L"]))
async def gpt_handler(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        name = message.from_user.first_name

        if len(message.command) < 2:
            await message.reply_text(f"Hello {name}, I am Lucy. How can I help you today?")
            return

        query = message.text.split(' ', 1)[1]
        messages = [Messages(content=query, role="user")]

        lexica_client = AsyncClient()
        try:
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            content = extract_content(response)
            await message.reply_text(content)
        except Exception as e:
            await message.reply_text(f"An error occurred: {e}")
        finally:
            await lexica_client.close()

    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {e}")

@pbot.on_message(filters.command(["gpt", "ai", "ask", "Master"], prefixes=["+", ".", "/", "-", "?", "$", "#", "&"]))
async def chat_gpt(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        name = message.from_user.first_name

        if len(message.command) < 2:
            await message.reply_text(f"Hello {name}, how can I assist you today?")
            return

        query = message.text.split(' ', 1)[1]
        messages = [Messages(content=query, role="user")]

        lexica_client = AsyncClient()
        try:
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            content = extract_content(response)
            await message.reply_text(content)
        except Exception as e:
            await message.reply_text(f"An error occurred: {e}")
        finally:
            await lexica_client.close()

    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {e}")

@pbot.on_message(filters.command(["ssis"], prefixes=["a", "A"]))
async def chat_annie(client: Client, message: Message):
    try:
        await client.send_chat_action(message.chat.id, ChatAction.RECORD_AUDIO)
        name = message.from_user.first_name

        if len(message.command) < 2:
            await message.reply_text(f"Hello {name}, I am Lucy. How can I assist you today?")
            return

        query = message.text.split(' ', 1)[1]
        messages = [Messages(content=query, role="user")]

        lexica_client = AsyncClient()
        try:
            response = await lexica_client.ChatCompletion(messages, languageModels.gpt)
            content = extract_content(response)
            tts = gTTS(text=content, lang='en')
            audio_file = 'response.mp3'
            tts.save(audio_file)
            await client.send_voice(chat_id=message.chat.id, voice=audio_file)
        except Exception as e:
            await message.reply_text(f"An error occurred: {e}")
        finally:
            await lexica_client.close()
            if os.path.exists(audio_file):
                os.remove(audio_file)

    except Exception as e:
        await message.reply_text(f"An unexpected error occurred: {e}")

import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message

# Define conversation states
SUBTITLE, VIDEO = range(2)

# Initialize the Pyrogram Client
api_id = "7391573"  # Replace with your API ID
api_hash = "1f20df54dfd91bcee05278d3b01da2c7"  # Replace with your API hash
bot_token = "6449794069:AAGDIZLMmHm17PBunAb840ttSYeuggPsOrY"  # Replace with your bot token

app = Client("encoder_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Dictionary to store user data during the conversation
user_data = {}

# Callback function to start the conversation
@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("Welcome to the Encoder Bot[!] This is [Beta](https://t.me/EncoderXBot) Version")
    await message.reply_text("Please send the subtitle file.")
    user_id = message.from_user.id
    user_data[user_id] = {}  # Create an empty user data dictionary
    user_data[user_id]["state"] = SUBTITLE  # Set the initial state to SUBTITLE

# Callback function to receive the subtitle file
@app.on_message(filters.document & filters.private)
async def receive_subtitle(_, message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.reply_text("Please start the conversation with /start.")
        return

    if user_data[user_id]["state"] == SUBTITLE:
        user_data[user_id]["subtitle_file"] = await message.download()
        await message.reply_text("Subtitle file received! Now, send me the video file.")
        user_data[user_id]["state"] = VIDEO  # Update the state to VIDEO
    else:
        await message.reply_text("Invalid state. Please start the conversation with /start again.")

# Callback function to receive the video file, burn subtitles, and send the processed video
@app.on_message(filters.document & filters.private)
async def receive_video(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.reply_text("Please start the conversation with /start.")
        return

    if user_data[user_id]["state"] == VIDEO:
        user_data[user_id]["video_file"] = await message.download()
        subtitle_file = user_data[user_id]["subtitle_file"]
        video_file = user_data[user_id]["video_file"]

        # Process the video with FFmpeg to burn in subtitles
        output_video_file = "output.mp4"
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-vf', f'subtitles={subtitle_file}:force_style=Fontsize=24',
            '-c:v', 'libx264', '-preset', 'fast',
            output_video_file
        ]

        try:
            subprocess.run(cmd, check=True)
            await app.send_video(chat_id=message.chat.id, video=open(output_video_file, "rb"))
            os.remove(output_video_file)
        except subprocess.CalledProcessError:
            await message.reply_text("An error occurred while processing the video.")

        # Clear user data
        del user_data[user_id]
    else:
        await message.reply_text("Invalid state. Please start the conversation with /start again.")

# Error handler for the conversation
@app.on_message(filters.command("cancel") & filters.private)
async def cancel(_, message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]  # Remove user data
    await message.reply_text("Operation canceled.")

if __name__ == '__main__':
    app.run()

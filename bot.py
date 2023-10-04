import os
import subprocess
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm

# Define conversation states
SUBTITLE, VIDEO, ENCODING = range(3)

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
    await message.reply_text("Welcome to the Encoder Bot! This is [Beta](https://t.me/EncoderXBot) Version")
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
        file_name, file_ext = os.path.splitext(message.document.file_name.lower())
        if file_ext not in (".srt", ".ass"):
            await message.reply_text("Invalid subtitle file format. Please send a .srt or .ass file.")
            return

        user_data[user_id]["subtitle_file"] = await message.download()
        await message.reply_text("Subtitle file received! Now, send me the video file.")
        user_data[user_id]["state"] = VIDEO  # Update the state to VIDEO
    else:
        await message.reply_text("Invalid state. Please start the conversation with /start again.")

# Callback function to receive the video file and start encoding with progress bars
@app.on_message(filters.document & filters.private)
async def receive_video(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.reply_text("Please start the conversation with /start.")
        return

    if user_data[user_id]["state"] == VIDEO:
        file_name, file_ext = os.path.splitext(message.document.file_name.lower())
        if file_ext not in (".mkv", ".mp4"):
            await message.reply_text("Invalid video file format. Please send an .mkv or .mp4 file.")
            return

        user_data[user_id]["video_file"] = await message.download()
        subtitle_file = user_data[user_id]["subtitle_file"]

        # Set the state to ENCODING and start encoding
        user_data[user_id]["state"] = ENCODING
        await message.reply_text("Video file received! Encoding has started. Please wait.")

        # Start encoding process with progress bar
        output_video_file = "output.mp4"
        cmd = [
            'ffmpeg',
            '-i', user_data[user_id]["video_file"],
            '-vf', f'subtitles={subtitle_file}:force_style=Fontsize=24',
            '-c:v', 'libx264', '-preset', 'fast',
            output_video_file
        ]

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with tqdm(total=100, position=0, desc="Encoding", unit="%", ascii=True) as progress_bar:
                while True:
                    output = process.stdout.readline()
                    if output == b'' and process.poll() is not None:
                        break
                    if output:
                        output_str = output.decode("utf-8")
                        if "frame=" in output_str:
                            progress = int(output_str.split("frame=")[-1].split(" ")[1].rstrip("%"))
                            progress_bar.update(progress - progress_bar.n)
                            # You can extract time, percentage, and total MB from 'output_str'
                            # Example: time = "00:02:30.45", percentage = 50.4%, total_mb = 1234MB

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

import os
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from tqdm import tqdm
from pydub import AudioSegment

# Define conversation states
VIDEO, SUBTITLE, ENCODING = range(3)

# Initialize the Pyrogram Client
api_id = "9976721"
api_hash = "3ef17a8cdb938335bd8ba292e6d816aa"
bot_token = "6916493009:AAET0al193Tfq4qNQHu3naCygFc9be6t5Kg"

app = Client("subtitle_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Dictionary to store user data during the conversation
user_data = {}

# Callback function to start the conversation
@app.on_message(filters.command("start"))
async def start(_, message):
    await message.reply_text("Welcome to the Subtitle Burner Bot! Send me the video file first.")
    user_id = message.from_user.id
    user_data[user_id] = {}  # Create an empty user data dictionary
    user_data[user_id]["state"] = VIDEO  # Set the initial state to VIDEO

# Callback function to receive the video file
@app.on_message(filters.document & filters.private)
async def receive_video(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.reply_text("Please start the conversation with /start.")
        return

    if user_data[user_id]["state"] == VIDEO:
        video_file = await message.download()
        user_data[user_id]["video_file"] = video_file
        await message.reply_text("Video file received! Now, send me the subtitle file (in .srt or .ass format).")
        user_data[user_id]["state"] = SUBTITLE  # Update the state to SUBTITLE
    else:
        await message.reply_text("Invalid state. Please start the conversation with /start again.")

# Callback function to receive the subtitle file and start burning subtitles onto the video
@app.on_message(filters.document & filters.private)
async def receive_subtitle(_, message: Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        await message.reply_text("Please start the conversation with /start.")
        return

    if user_data[user_id]["state"] == SUBTITLE:
        subtitle_file = await message.download()
        user_data[user_id]["subtitle_file"] = subtitle_file
        await message.reply_text("Subtitle file received! Burning subtitles onto the video. This may take a moment...")

        # Start the subtitle burning process
        video_file = user_data[user_id]["video_file"]
        output_video_file = "output.mp4"
        cmd = [
            'ffmpeg',
            '-i', video_file,
            '-vf', f'subtitles={subtitle_file}:force_style=Fontsize=24',
            '-c:v', 'libx264', '-preset', 'fast',
            output_video_file
        ]

        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            with tqdm(total=100, position=0, desc="Burning Subtitles", unit="%", ascii=True) as progress_bar:
                while True:
                    output = process.stderr.readline()
                    if output == b'' and process.poll() is not None:
                        break
                    if output:
                        output_str = output.decode("utf-8")
                        if "frame=" in output_str:
                            progress = int(output_str.split("frame=")[-1].split(" ")[1].rstrip("%"))
                            progress_bar.update(progress - progress_bar.n)

            await app.send_video(chat_id=message.chat.id, video=output_video_file)
            os.remove(output_video_file)
        except subprocess.CalledProcessError:
            await message.reply_text("An error occurred while burning subtitles onto the video.")

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

import os
import subprocess
from telegram import InputFile, Update
from telegram.ext import Updater, MessageHandler, Filters, CommandHandler, ConversationHandler, CallbackContext

# Define conversation states
SUBTITLE, VIDEO = range(2)

# Callback function to start the conversation
def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Welcome to the Encoder Bot! This is [Beta](https://t.me/EncoderXBot) Version")
    return SUBTITLE

# Callback function to receive the subtitle file
def receive_subtitle(update: Update, context: CallbackContext) -> int:
    subtitle_file = update.message.document.get_file()
    context.user_data['subtitle'] = subtitle_file.download()
    update.message.reply_text("Subtitle file received! Now, send me the video file.")
    return VIDEO

# Callback function to receive the video file, burn subtitles, and send the processed video
def receive_video(update: Update, context: CallbackContext) -> int:
    video_file = update.message.document.get_file()
    subtitle_file = context.user_data['subtitle']

    # Process the video with FFmpeg to burn in subtitles
    output_video_file = "output.mp4"
    subprocess.run([
        'ffmpeg',
        '-i', video_file.download_as_bytearray(),
        '-vf', f'subtitles={subtitle_file}:force_style=Fontsize=24',
        '-c:v', 'libx264', '-preset', 'fast',
        output_video_file
    ])

    # Send the processed video back to the user
    update.message.reply_video(video=InputFile(open(output_video_file, 'rb')))
    os.remove(output_video_file)

    return ConversationHandler.END

# Error handler for the conversation
def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("Operation canceled.")
    return ConversationHandler.END

def main():
    # Initialize the Telegram bot
    updater = Updater(token='6449794069:AAG0RoZ7nM8B90Yz3uL7z0ugsjiuaQKEh5E', use_context=True)
    dispatcher = updater.dispatcher

    # Create a conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SUBTITLE: [MessageHandler(Filters.document.mime_type("text/srt"), receive_subtitle)],
            VIDEO: [MessageHandler(Filters.document.mime_type("video/mp4"), receive_video)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the bot
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

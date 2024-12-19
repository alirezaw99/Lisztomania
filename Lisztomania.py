from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
import ffmpeg
import os
import re
import mutagen
from mutagen.easyid3 import EasyID3


# Global variables to track user state
user_states = {}

# Constants for states
STATE_IDLE = "idle"
STATE_ASK_DEMO_LENGTH = "ask_demo_length"
STATE_ASK_START_POINT = "ask_start_point"
STATE_EDIT_METADATA = "edit_metadata"


# Menu to show options for the uploaded file
async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    input_file = update.message.audio or update.message.voice
    if not input_file:
        await update.message.reply_text("Please send a valid audio file!")
        return

    # Save the file information in the user's state
    user_id = update.message.from_user.id
    user_states[user_id] = {
        "state": STATE_IDLE,
        "file_id": input_file.file_id,
        "file_name": f"{input_file.file_id}.mp3",
        "demo_length": None,
        "start_point": None,
    }

    # Present options to the user
    keyboard = [
        [InlineKeyboardButton("Give me the demo", callback_data="demo")],
        [InlineKeyboardButton("Change Caption", callback_data="caption")],
        [InlineKeyboardButton("Change File INFO", callback_data="change_metadata")],
        [InlineKeyboardButton("Cancel", callback_data="cancel")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("What do you want to do with this file?", reply_markup=reply_markup)

# Handle menu selection
async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.message is None:
        # If there's no message to edit, send a new message
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="Unknown option selected. Please try again."
        )
        return

    if user_id not in user_states:
        await query.edit_message_text("Please send an audio file first.")
        return

    # Handle user request
    match query.data:
        case "demo":
            user_states[user_id]["state"] = STATE_ASK_DEMO_LENGTH
            await query.edit_message_text("Enter the demo length in seconds (e.g., 20):")

        case "caption":
            # Show the second keyboard for caption options
            keyboard2 = [
                [InlineKeyboardButton("Change Caption", callback_data="change_caption")],
                [InlineKeyboardButton("Remove Caption", callback_data="remove_caption")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard2)
            await query.edit_message_text("Choose to Remove or Change Caption:", reply_markup=reply_markup)

        case "change_caption":
            # Ask for the new caption
            user_states[user_id]["state"] = "waiting_for_caption_text"
            await query.edit_message_text("Enter the new Caption:")

        case "remove_caption":
            # Remove the caption and send the file
            input_file_id = user_states[user_id]["file_id"]
            try:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=input_file_id,
                    caption="",  # No caption
                )
                user_states.pop(user_id, None)  # Clear user state
            except Exception as e:
                await query.edit_message_text(f"An error occurred while sending the file: {e}")
        
        case "change_metadata":
            user_states[user_id]["state"] = STATE_EDIT_METADATA
            input_file_id = user_states[user_id]["file_id"]

            # New keyboard for metadata options
            metadata_keyboard = [
                [InlineKeyboardButton("Change File Name", callback_data="change_filename")],
                [InlineKeyboardButton("Change Song Title", callback_data="change_title")],
                [InlineKeyboardButton("Change Artist Name", callback_data="change_artist")],
                [InlineKeyboardButton("Change Album Name", callback_data="change_album")],
                [InlineKeyboardButton("Change Genre", callback_data="change_genre")],
                [InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")],
            ]
            reply_markup = InlineKeyboardMarkup(metadata_keyboard)

            try:
                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=input_file_id,
                    caption="What metadata do you want to change?",
                    reply_markup=reply_markup
                )
            except Exception as e:
                await query.edit_message_text(f"An error occurred: {e}")
                
        case "cancel":
            user_states.pop(user_id, None)
            await query.edit_message_text("Operation cancelled.")

        case _:
            try:
                await query.edit_message_text("Unknown option selected.")
            except telegram.error.BadRequest:
                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text="Unknown option selected. Please try again."
                )


# Handle user replies for demo length and start point
async def handle_user_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        await update.message.reply_text("Please send an audio file first.")
        return

    user_state = user_states[user_id]
    if user_state["state"] == STATE_ASK_DEMO_LENGTH:
        try:
            demo_length = int(update.message.text)
            if demo_length <= 0:
                raise ValueError
            user_state["demo_length"] = demo_length
            user_state["state"] = STATE_ASK_START_POINT
            await update.message.reply_text(
                "Enter the start point of the demo in the format mm:ss (e.g., 0:30 or 2:15):"
            )
        except ValueError:
            await update.message.reply_text("Invalid length. Please enter a positive number (e.g., 20).")

    elif user_state["state"] == STATE_ASK_START_POINT:
        time_format = r"^\d+:[0-5]\d$"  # Regex to validate mm:ss format
        if not re.match(time_format, update.message.text):
            await update.message.reply_text("Invalid format. Use mm:ss (e.g., 0:30 or 2:15).")
            return

        # Convert start point to seconds
        minutes, seconds = map(int, update.message.text.split(":"))
        start_point = minutes * 60 + seconds
        user_state["start_point"] = start_point

        # Generate and send the demo
        await create_and_send_demo(update, context, user_state)
     
    #Change and send song with new Caption   
    elif user_state["state"] == "waiting_for_caption_text":
        # User entered the new caption
        caption = update.message.text
        user_state["caption"] = caption

        input_file_id = user_state["file_id"]

        try:
            await context.bot.send_audio(
                chat_id=update.message.chat_id,
                audio=input_file_id,
                caption=caption,  # Send with the new caption
            )
            user_states.pop(user_id, None)  # Clear user state
        except Exception as e:
            await update.message.reply_text(f"An error occurred while sending the file: {e}")
            
# Function to create and send the demo
async def create_and_send_demo(update: Update, context: ContextTypes.DEFAULT_TYPE, user_state):
    input_file_id = user_state["file_id"]
    input_path = user_state["file_name"]
    output_path = f"{input_file_id}_demo.ogg"
    demo_length = user_state["demo_length"]
    start_point = user_state["start_point"]

    # Download the file
    file = await context.bot.get_file(input_file_id)
    await file.download_to_drive(input_path)
    

    # Generate the demo
    try:
        ffmpeg.input(input_path, ss=start_point, t=demo_length).output(
            output_path, format="ogg", acodec="libopus", y=None 
        ).run(cmd="C:\\FFmpeg\\bin\\ffmpeg.exe")

        # Send the demo to the user
        with open(output_path, "rb") as voice_file:
            await update.message.reply_voice(voice=voice_file, caption="Here’s your voice demo!")

        # Clean up files
        os.remove(input_path)
        os.remove(output_path)
        user_states.pop(update.message.from_user.id, None)

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
        # Clean up input file if an error occurs
        if os.path.exists(input_path):
            os.remove(input_path)

async def handle_metadata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if user_id not in user_states or user_states[user_id]["state"] != STATE_EDIT_METADATA:
        await query.edit_message_text("Please send an audio file first.")
        return

    input_file_id = user_states[user_id]["file_id"]
    file_name = user_states[user_id]["file_name"]

    match query.data:
        case "change_filename":
            user_states[user_id]["state"] = "waiting_for_filename"
            await query.edit_message_text("Enter the new file name (without extension):")

        case "change_title":
            user_states[user_id]["state"] = "waiting_for_title"
            await query.edit_message_text("Enter the new song title:")

        case "change_artist":
            user_states[user_id]["state"] = "waiting_for_artist"
            await query.edit_message_text("Enter the new artist name:")

        case "change_album":
            user_states[user_id]["state"] = "waiting_for_album"
            await query.edit_message_text("Enter the new album name:")

        case "change_genre":
            user_states[user_id]["state"] = "waiting_for_genre"
            await query.edit_message_text("Enter the new genre:")

        case "main_menu":
            # Return to the main menu
            user_states[user_id]["state"] = STATE_IDLE
            await query.edit_message_text("Returning to the main menu. Select an option:")

async def handle_metadata_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_states:
        await update.message.reply_text("Please send an audio file first.")
        return

    user_state = user_states[user_id]
    input_file_id = user_state["file_id"]
    file_name = user_state["file_name"]

    try:
        if user_state["state"] == "waiting_for_filename":
            new_file_name = update.message.text + ".mp3"
            os.rename(file_name, new_file_name)
            user_state["file_name"] = new_file_name
            await update.message.reply_text(f"File name changed to {new_file_name}.")

        elif user_state["state"] == "waiting_for_title":
            audio = EasyID3(file_name)
            audio["title"] = update.message.text
            audio.save()
            await update.message.reply_text("Song title updated.")

        elif user_state["state"] == "waiting_for_artist":
            audio = EasyID3(file_name)
            audio["artist"] = update.message.text
            audio.save()
            await update.message.reply_text("Artist name updated.")

        elif user_state["state"] == "waiting_for_album":
            audio = EasyID3(file_name)
            audio["album"] = update.message.text
            audio.save()
            await update.message.reply_text("Album name updated.")

        elif user_state["state"] == "waiting_for_genre":
            audio = EasyID3(file_name)
            audio["genre"] = update.message.text
            audio.save()
            await update.message.reply_text("Genre updated.")

        # Keep the metadata keyboard open
        metadata_keyboard = [
            [InlineKeyboardButton("Change File Name", callback_data="change_filename")],
            [InlineKeyboardButton("Change Song Title", callback_data="change_title")],
            [InlineKeyboardButton("Change Artist Name", callback_data="change_artist")],
            [InlineKeyboardButton("Change Album Name", callback_data="change_album")],
            [InlineKeyboardButton("Change Genre", callback_data="change_genre")],
            [InlineKeyboardButton("Back to Main Menu", callback_data="main_menu")],
        ]
        reply_markup = InlineKeyboardMarkup(metadata_keyboard)

        await context.bot.send_audio(
            chat_id=update.message.chat_id,
            audio=input_file_id,
            caption="What else do you want to change?",
            reply_markup=reply_markup
        )

    except Exception as e:
        await update.message.reply_text(f"An error occurred: {e}")
                  
#Replys to /start command
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(f'Hello {update.effective_user.first_name} Wellcome to Lisztomania Music Editor BOT! \nSend me any Music File to Edit and get Demos.')

# Main function
def main():
    app = ApplicationBuilder().token("7776121371:AAEUm4yXqwMaZZPqOwtxRo3DP5wohFKTTOU").build()

    # Handlers
    app.add_handler(CommandHandler('start',start_handler))
    app.add_handler(MessageHandler(filters.AUDIO | filters.VOICE, handle_audio))
    app.add_handler(CallbackQueryHandler(handle_menu))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_reply))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

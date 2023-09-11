from telegram import Update
from telegram.ext import  ContextTypes, CommandHandler, ApplicationBuilder

async def start(update : Update, context : ContextTypes.DEFAULT_TYPE) -> None :
    await update.message.reply_text(f'Hello {update.effective_user.first_name} Wellcome to Lisztomania') 
    # context.bot.send_message(chat_id=update.effective_chat.id, text='Hello! I\'m Lisztomania. \n You can convert your music to voice message with me. \n And don\'t forget to Stay @Biskiviti ')

app = ApplicationBuilder().token('Token').build()
start_handler = CommandHandler('start', start)
app.add_handler(start_handler)

app.run_polling()

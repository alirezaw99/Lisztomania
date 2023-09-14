from telegram import Update , ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import   (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import logging
from pydub import AudioSegment 

#Enable logging
logging.basicConfig(format= "%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO) 
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

AUDIO = 0


#Define Command Handlers
async def start(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :

    await update.message.reply_text("Hi! My name is Lisztomania Bot. I will Convert Audio files to Voice for you. "
        "Please send your Audio file : \n\n"
        "Send /cancel to cancel the operation"
    )
        
    return AUDIO


async def audio(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    audio_file = await update.message.audio.get_file()
    await audio_file.download_to_drive('user_audio.mp3')
    logger.info(f'Audio of user {user.first_name} is downloaded to drive')
    
    song = AudioSegment.from_file('./user_audio.mp3')
    song.export('user_audio.ogg', format='ogg')
    
    await update.message.reply_voice('./user_audio.ogg')
    
    return ConversationHandler.END


async def cancel(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    logging.info(f'{user.first_name} cancelled conversation')
    await update.message.reply_text('Bye!')
    
    return ConversationHandler.END
        
 
     
#Run Bot
def main() -> None:
    app = Application.builder().token('6571724046:AAGqsTLfv2qE4EOZyj5WrMBLH2V35ABxZJo').build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            AUDIO: [MessageHandler(filters.AUDIO, audio)]
        }, fallbacks=[CommandHandler('cancel', cancel)]             
    )
    app.add_handler(conv_handler)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == '__main__':
    main()
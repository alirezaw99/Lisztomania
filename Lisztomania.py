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


#Enable logging
logging.basicConfig(format= "%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO) 
logging.getLogger('httpx').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

AUDIO = 0


#Define Command Handlers
async def start(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    reply_keyboard = [['Boy', 'Girl', 'Other']]
    
    await update.message.reply_text("Hi! My name is Lisztomania Bot. I will Convert Audio files to Voice for you. "
        "Please send your Audio file : \n\n"
        "Send /cancel to cancel the operation"
    )
        
    return AUDIO

'''
async def gender(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    logger.info(f'{user.first_name} is {update.message.text}')
    
    await update.message.reply_text('Got it!, Now send me Your Photo so i see what you look like'
                                    , reply_markup=ReplyKeyboardRemove())
        
    return PHOTO
'''   

async def audio(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    audio_file = await update.message.audio.get_file()
    await audio_file.download_to_drive('user_audio.mp3')
    logger.info(f'Audio of user {user.first_name} is downloaded to drive')
    await update.message.reply_text('Audio Recieved!')
    
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
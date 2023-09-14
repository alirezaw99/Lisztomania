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
GENDER , PHOTO, LOCATION, BIO = range(4)
#Define Command Handlers
async def start(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    reply_keyboard = [['Boy', 'Girl', 'Other']]
    
    await update.message.reply_text("Hi! My name is Professor Bot. I will hold a conversation with you. "
        "Send /cancel to stop talking to me.\n\n"
        "Are you a boy or a girl?", 
        reply_markup = ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder='Boy or Girl ?'
        ))
    return GENDER
async def gender(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    logger.info(f'{user.first_name} is {update.message.text}')
    
    await update.message.reply_text('Got it!, Now send me Your Photo so i see what you look like'
                                    , reply_markup=ReplyKeyboardRemove())
    
    
    
    return PHOTO
   
async def photo(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive('user_photo.jpg')
    logger.info(f'Photo of user {user.first_name} --> {photo_file.file_id} in {photo_file.file_path}')
    await update.message.reply_text('Gorgeous!')
    
    return ConversationHandler.END
async def cancel(update : Update, context : ContextTypes.DEFAULT_TYPE) -> int :
    user = update.message.from_user
    logging.info(f'{user.first_name} cancelled conversation')
    await update.message.reply_text('Bye!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END
        
 
     
#Run Bot
def main() -> None:
    app = Application.builder().token('6571724046:AAGqsTLfv2qE4EOZyj5WrMBLH2V35ABxZJo').build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            GENDER: [MessageHandler(filters.Regex("^(Boy|Girl|Other)$"), gender)],
            PHOTO: [MessageHandler(filters.PHOTO    , photo)]
        }, fallbacks=[CommandHandler('cancel', cancel)]            
    )
    app.add_handler(conv_handler)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == '__main__':
    main()
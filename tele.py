import telebot
from myAPI import token,chatID


def telegram_bot(token,text):
    try:
        bot = telebot.TeleBot(token)
        bot.send_message(chat_id=chatID, text=text)
    except:
        c=1

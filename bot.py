import telebot
from helper import CheggHelper
import os

bot = telebot.TeleBot('YOUR_BOT_TOKEN', parse_mode=None)
obj = CheggHelper()

@bot.message_handler(commands=['ans'])
def send_ans(message):
    try:
        ques_link = message.text.split(' ')[1]
        # print(ques_link)
        stat, filex, captionx = obj.getQAns(ques_link)
        if stat == True:
            bot.send_document(message.chat.id, open(filex, 'rb'), caption=captionx, reply_to_message_id=message.message_id)
            os.remove(filex)
        else:
            bot.reply_to(message, captionx)
    except Exception as e:
        bot.reply_to(message, str(e))

bot.polling()
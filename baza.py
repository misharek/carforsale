import telebot

bot = telebot.TeleBot("8117385329:AAFwTXqVa8Y6VTfoZs64wgwxIiG6xhowfF8")


@bot.message_handler(commands=["start"])
def handle_start(message):
    bot.send_message(message.chat.id, "владзьо проверка")


@bot.message_handler(commands=["help"])
def handle_start(message):
    bot.send_message(message.chat.id, "help information")


@bot.message_handler(commands=["aboutus"])
def handle_start(message):
    bot.send_message(message.chat.id, "about us")


bot.infinity_polling()

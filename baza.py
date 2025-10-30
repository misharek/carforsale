import telebot

bot = telebot.TeleBot("8117385329:AAFwTXqVa8Y6VTfoZs64wgwxIiG6xhowfF8")


@bot.message_handler(commands=["start"])
def main(message):
    bot.send_message(
        message.chat.id,
        f"Привіт,{message.from_user.first_name}",
    )


@bot.message_handler(commands=["help"])
def main(message):
    bot.send_message(
        message.chat.id, "<b>help</b> <em><u> information</u></em>", parse_mode="html"
    )


@bot.message_handler(commands=["aboutus"])
def handle_start(message):
    bot.send_message(message.chat.id, "about us")


bot.infinity_polling()

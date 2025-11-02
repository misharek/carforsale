import telebot

bot = telebot.TeleBot("8117385329:AAFwTXqVa8Y6VTfoZs64wgwxIiG6xhowfF8")


@bot.message_handler(commands=["start"])
def main(message):
    bot.send_message(
        message.chat.id,
        f"Привіт,{message.from_user.first_name}",
    )


help_text = (
    "CarForSaleBot — це ваш особистий інструмент для швидкої та зручної купівлі та продажу автомобілів у Telegram.\n\n"
    "**Що ви можете робити з CarForSaleBot:**\n\n"
    "/sale - Легко продати своє авто: Розмістіть оголошення за кілька хвилин, додайте фото та детальний опис.\n\n"
    "/buy - Знайти авто мрії: Переглядайте тисячі оголошень, фільтруйте за маркою, моделлю, ціною та іншими параметрами."
)


@bot.message_handler(commands=["help"])
def main(message):
    bot.send_message(message.chat.id, text=help_text, parse_mode="Markdown")


@bot.message_handler(commands=["aboutus"])
def handle_start(message):
    bot.send_message(message.chat.id, "about us")


bot.infinity_polling()

def get_telegram_username(message):
    telegram_username = message.from_user.first_name
    return telegram_username

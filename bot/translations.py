translations = [
    {
    'en': 'Hello there!\nThis bot will allow you to save everything right to the Notion page.',
    'ru': 'Привет! Этот бот позволит тебе сохранить всё сразу на страницу Ноушен.',
    },
    {
    'en': "Can't find notion link. Please begin with /start command.",
    'ru': "Не удалось найти ссылку Ноушен. Пожалуйста начтите с комманды /start",
    },
    {
    'en': "Can't find user. Please begin with /start command.",
    'ru': "Не удалось найти пользователя. Пожалуйста начтине с комманды /start",
    },
    {
    'en': "Title was changed! Please refresh page in the main menu below.",
    'ru': "Название поменялось! Не забудьте обновить страницу через главное меню /",
    },
    
]

main_locale = 'ru'
current_locale = 'ru'

def localize(text_to_translate:str):
    if(main_locale == current_locale):
        return text_to_translate
        
    for translate in translations:
        if(translate['ru'] == text_to_translate):
            return translate[current_locale]

    return text_to_translate

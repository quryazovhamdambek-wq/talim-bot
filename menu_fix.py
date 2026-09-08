from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

import handlers


def _main_keyboard(lang: str):
    t = handlers.t
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_vacancies")), KeyboardButton(text=t(lang, "btn_post_vacancy"))],
            [KeyboardButton(text=t(lang, "btn_post_resume")), KeyboardButton(text=t(lang, "btn_profile"))],
            [KeyboardButton(text=t(lang, "btn_my_listings")), KeyboardButton(text=t(lang, "btn_language"))],
            [KeyboardButton(text="🎓 O‘qish")],
        ],
        resize_keyboard=True,
    )


handlers.get_main_keyboard = _main_keyboard

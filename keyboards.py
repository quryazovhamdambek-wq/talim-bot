from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📢 Vakansiya joylash"), KeyboardButton(text="📝 Rezyume joylash")],
            [KeyboardButton(text="🔍 Vakansiyalarni ko'rish"), KeyboardButton(text="👤 Mening ma'lumotlarim")]
        ],
        resize_keyboard=True
    )

def region_keyboard():
    regions = [
        "Toshkent shahri", "Toshkent viloyati", "Andijon", "Buxoro", 
        "Farg'ona", "Jizzax", "Xorazm", "Namangan", 
        "Navoiy", "Qashqadaryo", "Samarqand", "Sirdaryo", "Surxondaryo", "Qoraqalpog'iston"
    ]
    buttons = [[KeyboardButton(text=r)] for r in regions]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

def work_format_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Offline"), KeyboardButton(text="Online"), KeyboardButton(text="Gibrid")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def moderation_keyboard(vacancy_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Tasdiqlash (Kanalga)", callback_data=f"approve_{vacancy_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{vacancy_id}")
            ]
        ]
    )

def apply_keyboard(vacancy_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Rezyume yuborish / Bog'lanish", callback_data=f"apply_{vacancy_id}")]
        ]
    )
  

from aiogram import Router, F
from aiogram.types import Message, BotCommand
from aiogram.fsm.context import FSMContext

from handlers import get_main_keyboard, get_user_lang

router = Router()

MENU_TEXT = {
    "uz": "🎓 <b>TA'LIM HUB</b>\n━━━━━━━━━━━━━━━━━━\n💼 Ta'lim sohasida ish toping yoki vakansiya joylang.\n\n🚀 <b>Tezkor bo'limlar</b>\n🔎 Vakansiyalar — mos ishlarni toping\n🏢 Vakansiya — ish o'rni e'lon qiling\n📝 Rezyume — o'zingizni ish beruvchilarga taniting\n👤 Profil — ma'lumotlaringizni ko'ring\n\n💡 <i>Har bir e'lon moderatsiyadan o'tadi.</i>\nQuyidagi menyudan foydalaning 👇",
    "ru": "🎓 <b>TA'LIM HUB</b>\n━━━━━━━━━━━━━━━━━━\n💼 Найдите работу в сфере образования или разместите вакансию.\n\n🚀 <b>Быстрые разделы</b>\n🔎 Вакансии — найдите подходящую работу\n🏢 Вакансия — разместите вакансию\n📝 Резюме — представьте себя работодателям\n👤 Профиль — ваши данные\n\n💡 <i>Каждое объявление проходит модерацию.</i>\nИспользуйте меню ниже 👇",
    "en": "🎓 <b>TA'LIM HUB</b>\n━━━━━━━━━━━━━━━━━━\n💼 Find an education job or post a vacancy.\n\n🚀 <b>Quick sections</b>\n🔎 Vacancies — find suitable jobs\n🏢 Vacancy — post a job\n📝 Resume — introduce yourself to employers\n👤 Profile — your information\n\n💡 <i>Every listing goes through moderation.</i>\nUse the menu below 👇",
}

@router.message(F.text == "/menu")
async def modern_menu(message: Message, state: FSMContext):
    await state.clear()
    lang = await get_user_lang(message.from_user.id)
    await message.answer(
        MENU_TEXT.get(lang, MENU_TEXT["uz"]),
        reply_markup=get_main_keyboard(lang),
        parse_mode="HTML",
    )

async def setup_commands(bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="🎓 Botni boshlash"),
        BotCommand(command="menu", description="🏠 Asosiy menyu"),
        BotCommand(command="help", description="ℹ️ Yordam"),
    ])

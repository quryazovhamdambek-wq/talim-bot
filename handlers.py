from aiogram import Router, F
from aiogram.types import Message

router = Router()

# 1. "Vakansiyalarni ko'rish" tugmasi uchun
@router.message(F.text == "🔍 Vakansiyalarni ko'rish")
async def show_vacancies_handler(message: Message):
    # Hozircha oddiy xabar qaytaradi (bazaga ulab ulgurmagan bo'lsangiz xato bermasligi uchun)
    await message.answer("📄 Hozircha faol vakansiyalar mavjud emas yoki bo'lim sozlanmoqda.")

# 2. "Mening ma'lumotlarim" tugmasi uchun
@router.message(F.text == "👤 Mening ma'lumotlarim")
async def my_profile_handler(message: Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Mavjud emas"
    
    text = (
        f"👤 **Sizning profilingiz:**\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"✍️ Ism: {user.full_name}\n"
        f"🌐 Username: {username}"
    )
    await message.answer(text, parse_mode="Markdown")

# 3. "Rezyume joylash" tugmasi uchun (agar u ham ishlamayotgan bo'lsa)
@router.message(F.text == "📝 Rezyume joylash")
async def post_resume_handler(message: Message):
    await message.answer("📝 Rezyume joylash bo'limi tez orada ishga tushadi!")
    

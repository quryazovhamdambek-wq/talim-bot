from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# Asosiy menyu tugmalari
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Vakansiyalarni ko'rish"), KeyboardButton(text="🏢 Vakansiya joylash")],
            [KeyboardButton(text="📝 Rezyume joylash"), KeyboardButton(text="👤 Mening ma'lumotlarim")]
        ],
        resize_keyboard=True
    )

# /start buyrug'i
@router.message(F.text == "/start")
async def start_handler(message: Message):
    await message.answer(
        "Assalomu alaykum! Ta'lim yo'nalishidagi vakansiya va rezyume botiga xush kelibsiz.",
        reply_markup=get_main_keyboard()
    )

# --- 1. MENING MA'LUMOTLARIM ---
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

# --- 2. VAKANSIYALARNI KO'RISH ---
@router.message(F.text == "🔍 Vakansiyalarni ko'rish")
async def show_vacancies_handler(message: Message):
    await message.answer("📄 Hozircha faol vakansiyalar bazada mavjud emas.")

# --- 3. REZYUME JOYLASH ---
@router.message(F.text == "📝 Rezyume joylash")
async def post_resume_handler(message: Message):
    await message.answer("📝 Rezyume joylash bo'limi tez orada ishga tushadi!")

# --- 4. VAKANSIYA JOYLASH (FSM QISMI) ---
# Ish beruvchi tugmani bosganda boshlanadigan qism
@router.message(F.text == "🏢 Vakansiya joylash")
async def vacancy_start(message: Message, state: FSMContext):
    await message.answer(
        "🏢 Vakansiya berish uchun tashkilot nomini kiriting:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
            resize_keyboard=True
        )
    )
    # Bu yerga o'zingizning FSM state'ingizni ulab qo'yasiz
    # Masalan: await state.set_state(VacancyState.company_name)

# Bekor qilish tugmasi
@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Amaliyot bekor qilindi.", reply_markup=get_main_keyboard())
    

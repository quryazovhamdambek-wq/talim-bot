from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database import async_session, User, Vacancy

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

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def get_work_format_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Offline"), KeyboardButton(text="Online")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

async def get_or_create_user(user_id: int, full_name: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, full_name=full_name)
            session.add(user)
            await session.commit()
        return user

# FSM holatlari - vakansiya joylash
class VacancyState(StatesGroup):
    company_name = State()
    title = State()
    subject = State()
    requirements = State()
    salary = State()
    region = State()
    work_format = State()
    contact = State()

# /start buyrug'i
@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Assalomu alaykum! Ta'lim yo'nalishidagi vakansiya va rezyume botiga xush kelibsiz.",
        reply_markup=get_main_keyboard()
    )

# --- MENING MA'LUMOTLARIM ---
@router.message(F.text == "👤 Mening ma'lumotlarim")
async def my_profile_handler(message: Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Mavjud emas"
    text = (
        f"👤 Sizning profilingiz:\n\n"
        f"🆔 ID: {user.id}\n"
        f"✍️ Ism: {user.full_name}\n"
        f"🌐 Username: {username}"
    )
    await message.answer(text)

# --- VAKANSIYALARNI KO'RISH ---
@router.message(F.text == "🔍 Vakansiyalarni ko'rish")
async def show_vacancies_handler(message: Message):
    async with async_session() as session:
        result = await session.execute(
            select(Vacancy).where(Vacancy.status == "approved")
        )
        vacancies = result.scalars().all()

    if not vacancies:
        await message.answer("📄 Hozircha faol vakansiyalar bazada mavjud emas.")
        return

    for v in vacancies:
        text = (
            f"🏢 {v.company_name}\n"
            f"📌 Lavozim: {v.title}\n"
            f"📚 Yo'nalish: {v.subject}\n"
            f"📋 Talablar: {v.requirements}\n"
            f"💰 Maosh: {v.salary}\n"
            f"📍 Hudud: {v.region}\n"
            f"🖥 Format: {v.work_format}\n"
            f"📞 Aloqa: {v.contact}"
        )
        await message.answer(text)

# --- REZYUME JOYLASH (hozircha placeholder) ---
@router.message(F.text == "📝 Rezyume joylash")
async def post_resume_handler(message: Message):
    await message.answer("📝 Rezyume joylash bo'limi tez orada ishga tushadi!")

# --- VAKANSIYA JOYLASH (FSM) ---
@router.message(F.text == "🏢 Vakansiya joylash")
async def vacancy_start(message: Message, state: FSMContext):
    await state.set_state(VacancyState.company_name)
    await message.answer(
        "🏢 Vakansiya berish uchun tashkilot nomini kiriting:",
        reply_markup=get_cancel_keyboard()
    )

@router.message(VacancyState.company_name)
async def vacancy_company_name(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text)
    await state.set_state(VacancyState.title)
    await message.answer("📌 Lavozim nomini kiriting (masalan: Matematika o'qituvchisi):")

@router.message(VacancyState.title)
async def vacancy_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(VacancyState.subject)
    await message.answer("📚 Fan/yo'nalishni kiriting:")

@router.message(VacancyState.subject)
async def vacancy_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(VacancyState.requirements)
    await message.answer("📋 Talablarni kiriting:")

@router.message(VacancyState.requirements)
async def vacancy_requirements(message: Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await state.set_state(VacancyState.salary)
    await message.answer("💰 Maoshni kiriting:")

@router.message(VacancyState.salary)
async def vacancy_salary(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await state.set_state(VacancyState.region)
    await message.answer("📍 Hududni kiriting:")

@router.message(VacancyState.region)
async def vacancy_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text)
    await state.set_state(VacancyState.work_format)
    await message.answer("🖥 Ish formatini tanlang:", reply_markup=get_work_format_keyboard())

@router.message(VacancyState.work_format, F.text.in_(["Offline", "Online"]))
async def vacancy_work_format(message: Message, state: FSMContext):
    await state.update_data(work_format=message.text.lower())
    await state.set_state(VacancyState.contact)
    await message.answer("📞 Aloqa uchun telefon yoki username kiriting:", reply_markup=get_cancel_keyboard())

@router.message(VacancyState.contact)
async def vacancy_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    user = message.from_user

    await get_or_create_user(user.id, user.full_name)

    async with async_session() as session:
        vacancy = Vacancy(
            employer_id=user.id,
            company_name=data["company_name"],
            title=data["title"],
            subject=data["subject"],
            requirements=data["requirements"],
            salary=data["salary"],
            region=data["region"],
            work_format=data["work_format"],
            contact=message.text,
            status="pending"
        )
        session.add(vacancy)
        await session.commit()

    await state.clear()
    await message.answer(
        "✅ Vakansiyangiz qabul qilindi va moderatsiyaga yuborildi!",
        reply_markup=get_main_keyboard()
    )

# Bekor qilish tugmasi (istalgan holatda ishlaydi)
@router.message(F.text == "❌ Bekor qilish")
async def cancel_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Amaliyot bekor qilindi.", reply_markup=get_main_keyboard())

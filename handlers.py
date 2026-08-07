import os
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import async_session, User, Vacancy
from keyboards import main_menu, region_keyboard, work_format_keyboard, moderation_keyboard, apply_keyboard

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

class VacancyState(StatesGroup):
    company_name = State()
    title = State()
    subject = State()
    requirements = State()
    salary = State()
    region = State()
    work_format = State()
    contact = State()

@router.message(CommandStart())
async def start_cmd(message: Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            new_user = User(user_id=message.from_user.id, full_name=message.from_user.full_name)
            session.add(new_user)
            await session.commit()
            
    await message.answer(
        f"Assalomu alaykum, {message.from_user.first_name}!\n"
        f"<b>Ta'lim vakansiyalari boti</b>ga xush kelibsiz.\nQuyidagilardan birini tanlang:",
        parse_mode="HTML",
        reply_markup=main_menu()
    )

# --- VAKANSIYA YIG'ISH FLOW ---
@router.message(F.text == "📢 Vakansiya joylash")
async def start_vacancy(message: Message, state: FSMContext):
    await state.set_state(VacancyState.company_name)
    await message.answer("Tashkilot / O'quv markaz nomini kiriting:", reply_markup=ReplyKeyboardRemove())

@router.message(VacancyState.company_name)
async def process_company(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text)
    await state.set_state(VacancyState.title)
    await message.answer("Bo'sh ish o'rni (Lavozim) nomini kiriting (masalan: Matematika o'qituvchisi):")

@router.message(VacancyState.title)
async def process_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(VacancyState.subject)
    await message.answer("Mavzu / Fan yo'nalishini kiriting:")

@router.message(VacancyState.subject)
async def process_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(VacancyState.requirements)
    await message.answer("Nomzodga qo'yiladigan talablarni kiriting:")

@router.message(VacancyState.requirements)
async def process_reqs(message: Message, state: FSMContext):
    await state.update_data(requirements=message.text)
    await state.set_state(VacancyState.salary)
    await message.answer("Kutilayotgan maosh (masalan: 5,000,000 - 8,000,000 so'm):")

@router.message(VacancyState.salary)
async def process_salary(message: Message, state: FSMContext):
    await state.update_data(salary=message.text)
    await state.set_state(VacancyState.region)
    await message.answer("Hududni tanlang:", reply_markup=region_keyboard())

@router.message(VacancyState.region)
async def process_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text)
    await state.set_state(VacancyState.work_format)
    await message.answer("Ish formatini tanlang:", reply_markup=work_format_keyboard())

@router.message(VacancyState.work_format)
async def process_format(message: Message, state: FSMContext):
    await state.update_data(work_format=message.text)
    await state.set_state(VacancyState.contact)
    await message.answer("Bog'lanish uchun telefon yoki Telegram username kiriting:", reply_markup=ReplyKeyboardRemove())

@router.message(VacancyState.contact)
async def process_contact(message: Message, state: FSMContext, bot: Bot):
    await state.update_data(contact=message.text)
    data = await state.get_data()
    await state.clear()

    async with async_session() as session:
        v = Vacancy(
            employer_id=message.from_user.id,
            company_name=data['company_name'],
            title=data['title'],
            subject=data['subject'],
            requirements=data['requirements'],
            salary=data['salary'],
            region=data['region'],
            work_format=data['work_format'],
            contact=data['contact']
        )
        session.add(v)
        await session.commit()
        await session.refresh(v)
        vacancy_id = v.id

    text = (
        f"<b>📢 YANGI VAKANSIYA #ID{vacancy_id}</b>\n\n"
        f"🏢 <b>Tashkilot:</b> {data['company_name']}\n"
        f"📌 <b>Lavozim:</b> {data['title']}\n"
        f"📚 <b>Fan:</b> {data['subject']}\n"
        f"🎯 <b>Talablar:</b> {data['requirements']}\n"
        f"💰 <b>Maosh:</b> {data['salary']}\n"
        f"📍 <b>Hudud:</b> {data['region']}\n"
        f"💻 <b>Format:</b> {data['work_format']}\n"
        f"📞 <b>Aloqa:</b> {data['contact']}"
    )

    await message.answer("✅ E'loningiz admin moderatsiyasiga yuborildi. Tasdiqlansa kanalda e'lon qilinadi!", reply_markup=main_menu())

    if ADMIN_ID:
        try:
            await bot.send_message(
                ADMIN_ID,
                f"📥 <b>Yangi vakansiya keldi (Moderatsiya):</b>\n\n{text}",
                parse_mode="HTML",
                reply_markup=moderation_keyboard(vacancy_id)
            )
        except Exception as e:
            print(f"Admin xabar yuborishda xato: {e}")

# --- ADMIN CALLBACKS (Kanalga Joylash) ---
@router.callback_query(F.data.startswith("approve_"))
async def approve_vacancy(call: CallbackQuery, bot: Bot):
    v_id = int(call.data.split("_")[1])
    async with async_session() as session:
        v = await session.get(Vacancy, v_id)
        if v:
            v.status = "approved"
            await session.commit()
            
            text = (
                f"📢 <b>VAKANSIYA: {v.title}</b>\n\n"
                f"🏢 <b>Tashkilot:</b> {v.company_name}\n"
                f"📚 <b>Fan:</b> {v.subject}\n"
                f"🎯 <b>Talablar:</b> {v.requirements}\n"
                f"💰 <b>Maosh:</b> {v.salary}\n"
                f"📍 <b>Hudud:</b> {v.region}\n"
                f"💻 <b>Format:</b> {v.work_format}\n\n"
                f"📞 <b>Aloqa:</b> {v.contact}"
            )
            
            if CHANNEL_ID:
                await bot.send_message(CHANNEL_ID, text, parse_mode="HTML", reply_markup=apply_keyboard(v_id))
                await call.message.edit_text(f"{call.message.text}\n\n✅ <b>Kanalga joylandi!</b>", parse_mode="HTML")

@router.callback_query(F.data.startswith("reject_"))
async def reject_vacancy(call: CallbackQuery):
    v_id = int(call.data.split("_")[1])
    async with async_session() as session:
        v = await session.get(Vacancy, v_id)
        if v:
            v.status = "rejected"
            await session.commit()
    await call.message.edit_text(f"{call.message.text}\n\n❌ <b>Rad etildi.</b>", parse_mode="HTML")
                         

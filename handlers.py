import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select, func

from database import async_session, User, Vacancy, Resume

router = Router()

ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
CHANNEL_ID = os.getenv("CHANNEL_ID")

SKIP_TEXT = "⏭ O'tkazib yuborish"


# ---------- KEYBOARDS ----------

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Vakansiyalarni ko'rish"), KeyboardButton(text="🏢 Vakansiya joylash")],
            [KeyboardButton(text="📝 Rezyume joylash"), KeyboardButton(text="👤 Mening ma'lumotlarim")],
            [KeyboardButton(text="📂 Mening e'lonlarim")]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True
    )

def get_cancel_skip_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=SKIP_TEXT)], [KeyboardButton(text="❌ Bekor qilish")]],
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

def get_confirm_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Tasdiqlash")],
            [KeyboardButton(text="❌ Bekor qilish")]
        ],
        resize_keyboard=True
    )

def get_admin_review_keyboard(kind: str, item_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{kind}:{item_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{kind}:{item_id}")
    ]])


async def get_or_create_user(user_id: int, full_name: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, full_name=full_name)
            session.add(user)
            await session.commit()
        return user


async def notify_admins(text: str, keyboard: InlineKeyboardMarkup, bot):
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, text, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            pass


# ---------- /start ----------

@router.message(F.text == "/start")
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 <b>Assalomu alaykum!</b>\n\n"
        "Bu — ta'lim sohasidagi ish va rezyume platformasi. Bu yerda siz:\n\n"
        "🏢 Vakansiya joylashingiz\n"
        "📝 Rezyume yaratishingiz\n"
        "🔍 Ochiq vakansiyalarni ko'rishingiz mumkin\n\n"
        "Boshlash uchun pastdagi tugmalardan birini tanlang 👇",
        reply_markup=get_main_keyboard(),
        parse_mode="HTML"
    )


# ---------- /help ----------

@router.message(F.text == "/help")
async def help_handler(message: Message):
    text = (
        "ℹ️ <b>Bot haqida qo'llanma</b>\n\n"
        "🏢 <b>Vakansiya joylash</b> — ish beruvchilar uchun, bo'sh o'rin e'lon qilish\n"
        "📝 <b>Rezyume joylash</b> — ish izlovchilar uchun, o'zingiz haqingizda ma'lumot qoldirish\n"
        "🔍 <b>Vakansiyalarni ko'rish</b> — tasdiqlangan barcha bo'sh o'rinlar\n"
        "📂 <b>Mening e'lonlarim</b> — joylagan e'lonlaringiz holati\n"
        "👤 <b>Mening ma'lumotlarim</b> — profil ma'lumotlari\n\n"
        "❗️ Har bir e'lon avval moderatsiyadan o'tadi, keyin e'lon qilinadi."
    )
    await message.answer(text, parse_mode="HTML")


# ---------- MENING MA'LUMOTLARIM ----------

@router.message(F.text == "👤 Mening ma'lumotlarim")
async def my_profile_handler(message: Message):
    user = message.from_user
    username = f"@{user.username}" if user.username else "Mavjud emas"
    text = (
        f"👤 <b>Sizning profilingiz</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"✍️ Ism: {user.full_name}\n"
        f"🌐 Username: {username}"
    )
    await message.answer(text, parse_mode="HTML")


# ---------- MENING E'LONLARIM ----------

@router.message(F.text == "📂 Mening e'lonlarim")
async def my_listings_handler(message: Message):
    user_id = message.from_user.id
    async with async_session() as session:
        vac_result = await session.execute(select(Vacancy).where(Vacancy.employer_id == user_id))
        vacancies = vac_result.scalars().all()
        res_result = await session.execute(select(Resume).where(Resume.candidate_id == user_id))
        resumes = res_result.scalars().all()

    if not vacancies and not resumes:
        await message.answer("📂 Sizda hali e'lonlar mavjud emas.")
        return

    status_emoji = {"pending": "⏳ Kutilmoqda", "approved": "✅ Tasdiqlangan", "rejected": "❌ Rad etilgan"}

    for v in vacancies:
        text = (
            f"🏢 <b>[Vakansiya]</b> {v.title} — {v.company_name}\n"
            f"Holat: {status_emoji.get(v.status, v.status)}"
        )
        await message.answer(text, parse_mode="HTML")

    for r in resumes:
        text = (
            f"📝 <b>[Rezyume]</b> {r.subject} — {r.full_name}\n"
            f"Holat: {status_emoji.get(r.status, r.status)}"
        )
        await message.answer(text, parse_mode="HTML")


# ---------- VAKANSIYALARNI KO'RISH ----------

@router.message(F.text == "🔍 Vakansiyalarni ko'rish")
async def show_vacancies_handler(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Vacancy).where(Vacancy.status == "approved"))
        vacancies = result.scalars().all()

    if not vacancies:
        await message.answer("📄 Hozircha faol vakansiyalar bazada mavjud emas.")
        return

    for v in vacancies:
        text = (
            f"🏢 <b>{v.company_name}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"📌 <b>Lavozim:</b> {v.title}\n"
            f"📚 <b>Yo'nalish:</b> {v.subject}\n"
            f"📋 <b>Talablar:</b> {v.requirements}\n"
            f"💰 <b>Maosh:</b> {v.salary}\n"
            f"📍 <b>Hudud:</b> {v.region}\n"
            f"🖥 <b>Format:</b> {v.work_format}\n"
            f"📞 <b>Aloqa:</b> {v.contact}"
        )
        await message.answer(text, parse_mode="HTML")


# ---------- VAKANSIYA JOYLASH (FSM) ----------

class VacancyState(StatesGroup):
    company_name = State()
    title = State()
    subject = State()
    requirements = State()
    salary = State()
    region = State()
    work_format = State()
    contact = State()
    confirm = State()


@router.message(F.text == "🏢 Vakansiya joylash")
async def vacancy_start(message: Message, state: FSMContext):
    await state.set_state(VacancyState.company_name)
    await message.answer("🏢 Tashkilot nomini kiriting:", reply_markup=get_cancel_keyboard())


@router.message(VacancyState.company_name)
async def vacancy_company_name(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text)
    await state.set_state(VacancyState.title)
    await message.answer("📌 Lavozim nomini kiriting:")


@router.message(VacancyState.title)
async def vacancy_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await state.set_state(VacancyState.subject)
    await message.answer("📚 Fan/yo'nalishni kiriting:")


@router.message(VacancyState.subject)
async def vacancy_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(VacancyState.requirements)
    await message.answer("📋 Talablarni kiriting (ixtiyoriy):", reply_markup=get_cancel_skip_keyboard())


@router.message(VacancyState.requirements)
async def vacancy_requirements(message: Message, state: FSMContext):
    value = None if message.text == SKIP_TEXT else message.text
    await state.update_data(requirements=value)
    await state.set_state(VacancyState.salary)
    await message.answer("💰 Maoshni kiriting (ixtiyoriy):", reply_markup=get_cancel_skip_keyboard())


@router.message(VacancyState.salary)
async def vacancy_salary(message: Message, state: FSMContext):
    value = None if message.text == SKIP_TEXT else message.text
    await state.update_data(salary=value)
    await state.set_state(VacancyState.region)
    await message.answer("📍 Hududni kiriting:", reply_markup=get_cancel_keyboard())


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
    await state.update_data(contact=message.text)
    data = await state.get_data()

    preview = (
        "📋 <b>Quyidagi ma'lumotlarni tekshiring:</b>\n\n"
        f"🏢 Tashkilot: {data['company_name']}\n"
        f"📌 Lavozim: {data['title']}\n"
        f"📚 Yo'nalish: {data['subject']}\n"
        f"📋 Talablar: {data.get('requirements') or '—'}\n"
        f"💰 Maosh: {data.get('salary') or '—'}\n"
        f"📍 Hudud: {data['region']}\n"
        f"🖥 Format: {data['work_format']}\n"
        f"📞 Aloqa: {data['contact']}"
    )
    await state.set_state(VacancyState.confirm)
    await message.answer(preview, reply_markup=get_confirm_keyboard(), parse_mode="HTML")


@router.message(VacancyState.confirm, F.text == "✅ Tasdiqlash")
async def vacancy_save(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    user = message.from_user
    await get_or_create_user(user.id, user.full_name)

    async with async_session() as session:
        vacancy = Vacancy(
            employer_id=user.id,
            company_name=data["company_name"],
            title=data["title"],
            subject=data["subject"],
            requirements=data.get("requirements") or "—",
            salary=data.get("salary") or "—",
            region=data["region"],
            work_format=data["work_format"],
            contact=data["contact"],
            status="pending"
        )
        session.add(vacancy)
        await session.commit()
        await session.refresh(vacancy)

    await state.clear()
    await message.answer("✅ Vakansiyangiz qabul qilindi va moderatsiyaga yuborildi!", reply_markup=get_main_keyboard())

    admin_text = (
        f"🆕 <b>Yangi vakansiya (#{vacancy.id})</b>\n\n"
        f"🏢 {vacancy.company_name}\n"
        f"📌 {vacancy.title}\n"
        f"📚 {vacancy.subject}\n"
        f"📋 {vacancy.requirements}\n"
        f"💰 {vacancy.salary}\n"
        f"📍 {vacancy.region}\n"
        f"🖥 {vacancy.work_format}\n"
        f"📞 {vacancy.contact}"
    )
    await notify_admins(admin_text, get_admin_review_keyboard("vacancy", vacancy.id), bot)


# ---------- REZYUME JOYLASH (FSM) ----------

class ResumeState(StatesGroup):
    full_name = State()
    phone = State()
    subject = State()
    experience = State()
    education = State()
    about = State()
    region = State()
    confirm = State()


@router.message(F.text == "📝 Rezyume joylash")
async def resume_start(message: Message, state: FSMContext):
    await state.set_state(ResumeState.full_name)
    await message.answer("📝 Rezyume yaratamiz. To'liq ismingizni kiriting:", reply_markup=get_cancel_keyboard())


@router.message(ResumeState.full_name)
async def resume_full_name(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)
    await state.set_state(ResumeState.phone)
    await message.answer("📞 Telefon raqamingizni kiriting:")


@router.message(ResumeState.phone)
async def resume_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(ResumeState.subject)
    await message.answer("📚 Qaysi fan/yo'nalish bo'yicha mutaxassissiz?")


@router.message(ResumeState.subject)
async def resume_subject(message: Message, state: FSMContext):
    await state.update_data(subject=message.text)
    await state.set_state(ResumeState.experience)
    await message.answer("💼 Ish tajribangizni yozing (ixtiyoriy):", reply_markup=get_cancel_skip_keyboard())


@router.message(ResumeState.experience)
async def resume_experience(message: Message, state: FSMContext):
    value = None if message.text == SKIP_TEXT else message.text
    await state.update_data(experience=value)
    await state.set_state(ResumeState.education)
    await message.answer("🎓 Ta'limingiz haqida yozing:", reply_markup=get_cancel_keyboard())


@router.message(ResumeState.education)
async def resume_education(message: Message, state: FSMContext):
    await state.update_data(education=message.text)
    await state.set_state(ResumeState.about)
    await message.answer("ℹ️ O'zingiz haqingizda qisqacha yozing (ixtiyoriy):", reply_markup=get_cancel_skip_keyboard())


@router.message(ResumeState.about)
async def resume_about(message: Message, state: FSMContext):
    value = None if message.text == SKIP_TEXT else message.text
    await state.update_data(about=value)
    await state.set_state(ResumeState.region)
    await message.answer("📍 Qaysi hududda ishlamoqchisiz?", reply_markup=get_cancel_keyboard())


@router.message(ResumeState.region)
async def resume_region(message: Message, state: FSMContext):
    await state.update_data(region=message.text)
    data = await state.get_data()

    preview = (
        "📋 <b>Quyidagi ma'lumotlarni tekshiring:</b>\n\n"
        f"✍️ Ism: {data['full_name']}\n"
        f"📞 Telefon: {data['phone']}\n"
        f"📚 Yo'nalish: {data['subject']}\n"
        f"💼 Tajriba: {data.get('experience') or '—'}\n"
        f"🎓 Ta'lim: {data['education']}\n"
        f"ℹ️ Haqida: {data.get('about') or '—'}\n"
        f"📍 Hudud: {data['region']}"
    )
    await state.set_state(ResumeState.confirm)
    await message.answer(preview, reply_markup=get_confirm_keyboard(), parse_mode="HTML")


@router.message(ResumeState.confirm, F.text == "✅ Tasdiqlash")
async def resume_save(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    user = message.from_user
    await get_or_create_user(user.id, user.full_name)

    async with async_session() as session:
        resume = Resume(
            candidate_id=user.id,
            full_name=data["full_name"],
            phone=data["phone"],
            subject=data["subject"],
            experience=data.get("experience") or "—",
            education=data["education"],
            about=data.get("about") or "—",
            region=data["region"],
            status="pending"
        )
        session.add(resume)
        await session.commit()
        await session.refresh(resume)

    await state.clear()
    await message.answer("✅ Rezyumeingiz qabul qilindi va moderatsiyaga yuborildi!", reply_markup=get_main_keyboard())

    admin_text = (
        f"🆕 <b>Yangi rezyume (#{resume.id})</b>\n\n"
        f"✍️ {resume.full_name}\n"
        f"📞 {resume.phone}\n"
        f"📚 {resume.subject}\n"
        f"💼 {resume.experience}\n"
        f"🎓 {resume.education}\n"
        f"ℹ️ {resume.about}\n"
        f"📍 {resume.region}"
    )
    await notify_admins(admin_text, get_admin_review_keyboard("resume", resume.id), bot)


# ---------- ADMIN: TASDIQLASH / RAD ETISH ----------

@router.callback_query(F.data.startswith("approve:") | F.data.startswith("reject:"))
async def admin_review_callback(callback: CallbackQuery, bot):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("Sizda ruxsat yo'q.", show_alert=True)
        return

    action, kind, item_id_str = callback.data.split(":")
    item_id = int(item_id_str)
    new_status = "approved" if action == "approve" else "rejected"

    async with async_session() as session:
        if kind == "vacancy":
            result = await session.execute(select(Vacancy).where(Vacancy.id == item_id))
            item = result.scalar_one_or_none()
        else:
            result = await session.execute(select(Resume).where(Resume.id == item_id))
            item = result.scalar_one_or_none()

        if not item:
            await callback.answer("Topilmadi yoki allaqachon ko'rib chiqilgan.", show_alert=True)
            return

        item.status = new_status
        await session.commit()

        recipient_id = item.employer_id if kind == "vacancy" else item.candidate_id

    await callback.message.edit_reply_markup(reply_markup=None)

    if new_status == "approved":
        await callback.message.answer(f"✅ #{item_id} tasdiqlandi.")
        try:
            await bot.send_message(recipient_id, "✅ E'loningiz tasdiqlandi va e'lon qilindi!")
        except Exception:
            pass

        if CHANNEL_ID and kind == "vacancy":
            channel_text = (
                f"🏢 <b>{item.company_name}</b>\n"
                f"━━━━━━━━━━━━━━\n"
                f"📌 <b>Lavozim:</b> {item.title}\n"
                f"📚 <b>Yo'nalish:</b> {item.subject}\n"
                f"📋 <b>Talablar:</b> {item.requirements}\n"
                f"💰 <b>Maosh:</b> {item.salary}\n"
                f"📍 <b>Hudud:</b> {item.region}\n"
                f"🖥 <b>Format:</b> {item.work_format}\n"
                f"📞 <b>Aloqa:</b> {item.contact}"
            )
            try:
                await bot.send_message(CHANNEL_ID, channel_text, parse_mode="HTML")
            except Exception:
                pass
    else:
        await callback.message.answer(f"❌ #{item_id} rad etildi.")
        try:
            await bot.send_message(recipient_id, "❌ Afsuski, e'loningiz rad etildi.")
        except Exception:
            pass

    await callback.answer()


# ---------- ADMIN: STATISTIKA ----------

@router.message(F.text == "/stats")
async def stats_handler(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    async with async_session() as session:
        total_vac = await session.scalar(select(func.count()).select_from(Vacancy))
        pending_vac = await session.scalar(select(func.count()).select_from(Vacancy).where(Vacancy.status == "pending"))
        approved_vac = await session.scalar(select(func.count()).select_from(Vacancy).where(Vacancy.status == "approved"))

        total_res = await session.scalar(select(func.count()).select_from(Resume))
        pending_res = await session.scalar(select(func.count()).select_from(Resume).where(Resume.status == "pending"))
        approved_res = await session.scalar(select(func.count()).select_from(Resume).where(Resume.status == "approved"))

        total_users = await session.scalar(select(func.count()).select_from(User))

    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: {total_users}\n\n"
        f"🏢 <b>Vakansiyalar:</b> {total_vac}\n"
        f"   ⏳ Kutilmoqda: {pending_vac}\n"
        f"   ✅ Tasdiqlangan: {approved_vac}\n\n"
        f"📝 <b>Rezyumelar:</b> {total_res}\n"
        f"   ⏳ Kutilmoqda: {pending_res}\n"
        f"   ✅ Tasdiqlangan: {approved_res}"
    )
    await message.answer(text, parse_mode="HTML")


# ---------- BEKOR QILISH ----------

            

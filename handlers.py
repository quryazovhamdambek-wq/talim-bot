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

LANGS = ["uz", "ru", "en"]

# ---------- TARJIMALAR ----------

TEXTS = {
    "uz": {
        "welcome": (
            "👋 <b>Assalomu alaykum!</b>\n\n"
            "Bu — ta'lim sohasidagi ish va rezyume platformasi. Bu yerda siz:\n\n"
            "🏢 Vakansiya joylashingiz\n"
            "📝 Rezyume yaratishingiz\n"
            "🔍 Ochiq vakansiyalarni ko'rishingiz mumkin\n\n"
            "Boshlash uchun pastdagi tugmalardan birini tanlang 👇"
        ),
        "choose_language": "🌐 Tilni tanlang:",
        "language_set": "✅ Til o'zbekchaga o'rnatildi.",
        "help": (
            "ℹ️ <b>Bot haqida qo'llanma</b>\n\n"
            "🏢 <b>Vakansiya joylash</b> — ish beruvchilar uchun, bo'sh o'rin e'lon qilish\n"
            "📝 <b>Rezyume joylash</b> — ish izlovchilar uchun, o'zingiz haqingizda ma'lumot qoldirish\n"
            "🔍 <b>Vakansiyalarni ko'rish</b> — tasdiqlangan barcha bo'sh o'rinlar\n"
            "📂 <b>Mening e'lonlarim</b> — joylagan e'lonlaringiz holati\n"
            "👤 <b>Mening ma'lumotlarim</b> — profil ma'lumotlari\n\n"
            "❗️ Har bir e'lon avval moderatsiyadan o'tadi, keyin e'lon qilinadi."
        ),
        "btn_vacancies": "🔍 Vakansiyalarni ko'rish",
        "btn_post_vacancy": "🏢 Vakansiya joylash",
        "btn_post_resume": "📝 Rezyume joylash",
        "btn_profile": "👤 Mening ma'lumotlarim",
        "btn_my_listings": "📂 Mening e'lonlarim",
        "btn_language": "🌐 Til",
        "btn_cancel": "❌ Bekor qilish",
        "btn_skip": "⏭ O'tkazib yuborish",
        "btn_confirm": "✅ Tasdiqlash",
        "btn_offline": "Offline",
        "btn_online": "Online",
        "cancelled": "Amaliyot bekor qilindi.",
        "profile_title": "👤 <b>Sizning profilingiz</b>",
        "id_label": "🆔 ID:",
        "name_label": "✍️ Ism:",
        "username_label": "🌐 Username:",
        "username_none": "Mavjud emas",
        "no_listings": "📂 Sizda hali e'lonlar mavjud emas.",
        "status_pending": "⏳ Kutilmoqda",
        "status_approved": "✅ Tasdiqlangan",
        "status_rejected": "❌ Rad etilgan",
        "listing_vacancy": "🏢 [Vakansiya]",
        "listing_resume": "📝 [Rezyume]",
        "status_label": "Holat:",
        "no_vacancies": "📄 Hozircha faol vakansiyalar bazada mavjud emas.",
        "v_position": "📌 Lavozim:",
        "v_subject": "📚 Yo'nalish:",
        "v_requirements": "📋 Talablar:",
        "v_salary": "💰 Maosh:",
        "v_region": "📍 Hudud:",
        "v_format": "🖥 Format:",
        "v_contact": "📞 Aloqa:",
        "ask_company": "🏢 Tashkilot nomini kiriting:",
        "ask_position": "📌 Lavozim nomini kiriting:",
        "ask_subject": "📚 Fan/yo'nalishni kiriting:",
        "ask_requirements": "📋 Talablarni kiriting (ixtiyoriy):",
        "ask_salary": "💰 Maoshni kiriting (ixtiyoriy):",
        "ask_region": "📍 Hududni kiriting:",
        "ask_format": "🖥 Ish formatini tanlang:",
        "ask_contact": "📞 Aloqa uchun telefon yoki username kiriting:",
        "vacancy_preview_title": "📋 <b>Quyidagi ma'lumotlarni tekshiring:</b>",
        "vacancy_saved": "✅ Vakansiyangiz qabul qilindi va moderatsiyaga yuborildi!",
        "ask_full_name": "📝 Rezyume yaratamiz. To'liq ismingizni kiriting:",
        "ask_phone": "📞 Telefon raqamingizni kiriting:",
        "ask_resume_subject": "📚 Qaysi fan/yo'nalish bo'yicha mutaxassissiz?",
        "ask_experience": "💼 Ish tajribangizni yozing (ixtiyoriy):",
        "ask_education": "🎓 Ta'limingiz haqida yozing:",
        "ask_about": "ℹ️ O'zingiz haqingizda qisqacha yozing (ixtiyoriy):",
        "ask_resume_region": "📍 Qaysi hududda ishlamoqchisiz?",
        "resume_preview_title": "📋 <b>Quyidagi ma'lumotlarni tekshiring:</b>",
        "resume_saved": "✅ Rezyumeingiz qabul qilindi va moderatsiyaga yuborildi!",
        "r_name": "✍️ Ism:",
        "r_phone": "📞 Telefon:",
        "r_experience": "💼 Tajriba:",
        "r_education": "🎓 Ta'lim:",
        "r_about": "ℹ️ Haqida:",
        "approved_notify": "✅ E'loningiz tasdiqlandi va e'lon qilindi!",
        "rejected_notify": "❌ Afsuski, e'loningiz rad etildi.",
    },
    "ru": {
        "welcome": (
            "👋 <b>Здравствуйте!</b>\n\n"
            "Это — платформа вакансий и резюме в сфере образования. Здесь вы можете:\n\n"
            "🏢 Разместить вакансию\n"
            "📝 Создать резюме\n"
            "🔍 Просмотреть открытые вакансии\n\n"
            "Выберите один из пунктов ниже, чтобы начать 👇"
        ),
        "choose_language": "🌐 Выберите язык:",
        "language_set": "✅ Язык установлен на русский.",
        "help": (
            "ℹ️ <b>Справка о боте</b>\n\n"
            "🏢 <b>Разместить вакансию</b> — для работодателей\n"
            "📝 <b>Разместить резюме</b> — для соискателей\n"
            "🔍 <b>Просмотр вакансий</b> — все одобренные вакансии\n"
            "📂 <b>Мои объявления</b> — статус ваших объявлений\n"
            "👤 <b>Мои данные</b> — информация профиля\n\n"
            "❗️ Каждое объявление сначала проходит модерацию."
        ),
        "btn_vacancies": "🔍 Просмотр вакансий",
        "btn_post_vacancy": "🏢 Разместить вакансию",
        "btn_post_resume": "📝 Разместить резюме",
        "btn_profile": "👤 Мои данные",
        "btn_my_listings": "📂 Мои объявления",
        "btn_language": "🌐 Язык",
        "btn_cancel": "❌ Отмена",
        "btn_skip": "⏭ Пропустить",
        "btn_confirm": "✅ Подтвердить",
        "btn_offline": "Офлайн",
        "btn_online": "Онлайн",
        "cancelled": "Действие отменено.",
        "profile_title": "👤 <b>Ваш профиль</b>",
        "id_label": "🆔 ID:",
        "name_label": "✍️ Имя:",
        "username_label": "🌐 Username:",
        "username_none": "Не указан",
        "no_listings": "📂 У вас пока нет объявлений.",
        "status_pending": "⏳ На рассмотрении",
        "status_approved": "✅ Одобрено",
        "status_rejected": "❌ Отклонено",
        "listing_vacancy": "🏢 [Вакансия]",
        "listing_resume": "📝 [Резюме]",
        "status_label": "Статус:",
        "no_vacancies": "📄 Пока нет активных вакансий.",
        "v_position": "📌 Должность:",
        "v_subject": "📚 Направление:",
        "v_requirements": "📋 Требования:",
        "v_salary": "💰 Зарплата:",
        "v_region": "📍 Регион:",
        "v_format": "🖥 Формат:",
        "v_contact": "📞 Контакт:",
        "ask_company": "🏢 Введите название организации:",
        "ask_position": "📌 Введите название должности:",
        "ask_subject": "📚 Введите предмет/направление:",
        "ask_requirements": "📋 Введите требования (необязательно):",
        "ask_salary": "💰 Введите зарплату (необязательно):",
        "ask_region": "📍 Введите регион:",
        "ask_format": "🖥 Выберите формат работы:",
        "ask_contact": "📞 Введите телефон или username для связи:",
        "vacancy_preview_title": "📋 <b>Проверьте данные:</b>",
        "vacancy_saved": "✅ Вакансия принята и отправлена на модерацию!",
        "ask_full_name": "📝 Создаём резюме. Введите ваше полное имя:",
        "ask_phone": "📞 Введите ваш номер телефона:",
        "ask_resume_subject": "📚 По какому предмету/направлению вы специалист?",
        "ask_experience": "💼 Опишите опыт работы (необязательно):",
        "ask_education": "🎓 Расскажите об образовании:",
        "ask_about": "ℹ️ Кратко о себе (необязательно):",
        "ask_resume_region": "📍 В каком регионе хотите работать?",
        "resume_preview_title": "📋 <b>Проверьте данные:</b>",
        "resume_saved": "✅ Резюме принято и отправлено на модерацию!",
        "r_name": "✍️ Имя:",
        "r_phone": "📞 Телефон:",
        "r_experience": "💼 Опыт:",
        "r_education": "🎓 Образование:",
        "r_about": "ℹ️ О себе:",
        "approved_notify": "✅ Ваше объявление одобрено и опубликовано!",
        "rejected_notify": "❌ К сожалению, ваше объявление отклонено.",
    },
    "en": {
        "welcome": (
            "👋 <b>Welcome!</b>\n\n"
            "This is a job and resume platform for the education sector. Here you can:\n\n"
            "🏢 Post a job vacancy\n"
            "📝 Create a resume\n"
            "🔍 Browse open vacancies\n\n"
            "Choose an option below to get started 👇"
        ),
        "choose_language": "🌐 Choose a language:",
        "language_set": "✅ Language set to English.",
        "help": (
            "ℹ️ <b>Bot guide</b>\n\n"
            "🏢 <b>Post vacancy</b> — for employers\n"
            "📝 <b>Post resume</b> — for job seekers\n"
            "🔍 <b>View vacancies</b> — all approved vacancies\n"
            "📂 <b>My listings</b> — status of your listings\n"
            "👤 <b>My profile</b> — profile info\n\n"
            "❗️ Every listing goes through moderation first."
        ),
        "btn_vacancies": "🔍 View vacancies",
        "btn_post_vacancy": "🏢 Post vacancy",
        "btn_post_resume": "📝 Post resume",
        "btn_profile": "👤 My profile",
        "btn_my_listings": "📂 My listings",
        "btn_language": "🌐 Language",
        "btn_cancel": "❌ Cancel",
        "btn_skip": "⏭ Skip",
        "btn_confirm": "✅ Confirm",
        "btn_offline": "Offline",
        "btn_online": "Online",
        "cancelled": "Action cancelled.",
        "profile_title": "👤 <b>Your profile</b>",
        "id_label": "🆔 ID:",
        "name_label": "✍️ Name:",
        "username_label": "🌐 Username:",
        "username_none": "Not set",
        "no_listings": "📂 You don't have any listings yet.",
        "status_pending": "⏳ Pending",
        "status_approved": "✅ Approved",
        "status_rejected": "❌ Rejected",
        "listing_vacancy": "🏢 [Vacancy]",
        "listing_resume": "📝 [Resume]",
        "status_label": "Status:",
        "no_vacancies": "📄 No active vacancies yet.",
        "v_position": "📌 Position:",
        "v_subject": "📚 Subject:",
        "v_requirements": "📋 Requirements:",
        "v_salary": "💰 Salary:",
        "v_region": "📍 Region:",
        "v_format": "🖥 Format:",
        "v_contact": "📞 Contact:",
        "ask_company": "🏢 Enter the organization name:",
        "ask_position": "📌 Enter the position title:",
        "ask_subject": "📚 Enter the subject/field:",
        "ask_requirements": "📋 Enter requirements (optional):",
        "ask_salary": "💰 Enter the salary (optional):",
        "ask_region": "📍 Enter the region:",
        "ask_format": "🖥 Choose the work format:",
        "ask_contact": "📞 Enter phone or username for contact:",
        "vacancy_preview_title": "📋 <b>Please review the details:</b>",
        "vacancy_saved": "✅ Your vacancy was accepted and sent for moderation!",
        "ask_full_name": "📝 Let's create your resume. Enter your full name:",
        "ask_phone": "📞 Enter your phone number:",
        "ask_resume_subject": "📚 What subject/field are you specialized in?",
        "ask_experience": "💼 Describe your work experience (optional):",
        "ask_education": "🎓 Tell us about your education:",
        "ask_about": "ℹ️ Briefly describe yourself (optional):",
        "ask_resume_region": "📍 Which region do you want to work in?",
        "resume_preview_title": "📋 <b>Please review the details:</b>",
        "resume_saved": "✅ Your resume was accepted and sent for moderation!",
        "r_name": "✍️ Name:",
        "r_phone": "📞 Phone:",
        "r_experience": "💼 Experience:",
        "r_education": "🎓 Education:",
        "r_about": "ℹ️ About:",
        "approved_notify": "✅ Your listing has been approved and published!",
        "rejected_notify": "❌ Unfortunately, your listing was rejected.",
    },
}


def t(lang: str, key: str) -> str:
    lang = lang if lang in LANGS else "uz"
    return TEXTS[lang].get(key, TEXTS["uz"].get(key, key))


def all_variants(key: str):
    return [TEXTS[l][key] for l in LANGS]


# ---------- FOYDALANUVCHI TILI ----------

async def get_or_create_user(user_id: int, full_name: str) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(user_id=user_id, full_name=full_name)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def get_user_lang(user_id: int) -> str:
    async with async_session() as session:
        result = await session.execute(select(User.language).where(User.user_id == user_id))
        lang = result.scalar_one_or_none()
        return lang or "uz"


async def set_user_lang(user_id: int, lang: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()
        if user:
            user.language = lang
            await session.commit()


# ---------- KEYBOARDS ----------

def get_main_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_vacancies")), KeyboardButton(text=t(lang, "btn_post_vacancy"))],
            [KeyboardButton(text=t(lang, "btn_post_resume")), KeyboardButton(text=t(lang, "btn_profile"))],
            [KeyboardButton(text=t(lang, "btn_my_listings")), KeyboardButton(text=t(lang, "btn_language"))]
        ],
        resize_keyboard=True
    )

def get_cancel_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "btn_cancel"))]],
        resize_keyboard=True
    )

def get_cancel_skip_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t(lang, "btn_skip"))], [KeyboardButton(text=t(lang, "btn_cancel"))]],
        resize_keyboard=True
    )

def get_work_format_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_offline")), KeyboardButton(text=t(lang, "btn_online"))],
            [KeyboardButton(text=t(lang, "btn_cancel"))]
        ],
        resize_keyboard=True
    )

def get_confirm_keyboard(lang: str):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t(lang, "btn_confirm"))],
            [KeyboardButton(text=t(lang, "btn_cancel"))]
        ],
        resize_keyboard=True
    )

def get_language_inline_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="setlang:uz"),
        InlineKeyboardButton(text="🇷🇺 Русский", callback_data="setlang:ru"),
        InlineKeyboardButton(text="🇬🇧 English", callback_data="setlang:en"),
    ]])

def get_admin_review_keyboard(kind: str, item_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve:{kind}:{item_id}"),
        InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject:{kind}:{item_id}")
    ]])


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
    user = await get_or_create_user(message.from_user.id, message.from_user.full_name)
    await message.answer(t(user.language, "welcome"), reply_markup=get_main_keyboard(user.language), parse_mode="HTML")


# ---------- /help ----------

@router.message(F.text == "/help")
async def help_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "help"), parse_mode="HTML")


# ---------- TIL TANLASH ----------

@router.message(F.text.in_(all_variants("btn_language")))
async def language_menu_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    await message.answer(t(lang, "choose_language"), reply_markup=get_language_inline_keyboard())


@router.callback_query(F.data.startswith("setlang:"))
async def set_language_callback(callback: CallbackQuery):
    new_lang = callback.data.split(":")[1]
    await get_or_create_user(callback.from_user.id, callback.from_user.full_name)
    await set_user_lang(callback.from_user.id, new_lang)

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(t(new_lang, "language_set"))
    await callback.message.answer(t(new_lang, "welcome"), reply_markup=get_main_keyboard(new_lang), parse_mode="HTML")
    await callback.answer()


# ---------- MENING MA'LUMOTLARIM ----------

@router.message(F.text.in_(all_variants("btn_profile")))
async def my_profile_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    user = message.from_user
    username = f"@{user.username}" if user.username else t(lang, "username_none")
    text = (
        f"{t(lang, 'profile_title')}\n"
        f"━━━━━━━━━━━━━━\n"
        f"{t(lang, 'id_label')} <code>{user.id}</code>\n"
        f"{t(lang, 'name_label')} {user.full_name}\n"
        f"{t(lang, 'username_label')} {username}"
    )
    await message.answer(text, parse_mode="HTML")


# ---------- MENING E'LONLARIM ----------

@router.message(F.text.in_(all_variants("btn_my_listings")))
async def my_listings_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)
    user_id = message.from_user.id

    async with async_session() as session:
        vac_result = await session.execute(select(Vacancy).where(Vacancy.employer_id == user_id))
        vacancies = vac_result.scalars().all()
        res_result = await session.execute(select(Resume).where(Resume.candidate_id == user_id))
        resumes = res_result.scalars().all()

    if not vacancies and not resumes:
        await message.answer(t(lang, "no_listings"))
        return

    status_key = {"pending": "status_pending", "approved": "status_approved", "rejected": "status_rejected"}

    for v in vacancies:
        text = (
            f"{t(lang, 'listing_vacancy')} {v.title} — {v.company_name}\n"
            f"{t(lang, 'status_label')} {t(lang, status_key.get(v.status, 'status_pending'))}"
        )
        await message.answer(text, parse_mode="HTML")

    for r in resumes:
        text = (
            f"{t(lang, 'listing_resume')} {r.subject} — {r.full_name}\n"
            f"{t(lang, 'status_label')} {t(lang, status_key.get(r.status, 'status_pending'))}"
        )
        await message.answer(text, parse_mode="HTML")


# ---------- VAKANSIYALARNI KO'RISH ----------

@router.message(F.text.in_(all_variants("btn_vacancies")))
async def show_vacancies_handler(message: Message):
    lang = await get_user_lang(message.from_user.id)

    async with async_session() as session:
        result = await session.execute(select(Vacancy).where(Vacancy.status == "approved"))
        vacancies = result.scalars().all()

    if not vacancies:
        await message.answer(t(lang, "no_vacancies"))
        return

    for v in vacancies:
        text = (
            f"🏢 <b>{v.company_name}</b>\n"
            f"━━━━━━━━━━━━━━\n"
            f"{t(lang, 'v_position')} {v.title}\n"
            f"{t(lang, 'v_subject')} {v.subject}\n"
            f"{t(lang, 'v_requirements')} {v.requirements}\n"
            f"{t(lang, 'v_salary')} {v.salary}\n"
            f"{t(lang, 'v_region')} {v.region}\n"
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


@router.message(F.text.in_(all_variants("btn_post_vacancy")))
async def vacancy_start(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await state.update_data(lang=lang)
    await state.set_state(VacancyState.company_name)
    await message.answer(t(lang, "ask_company"), reply_markup=get_cancel_keyboard(lang))


@router.message(VacancyState.company_name)
async def vacancy_company_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(company_name=message.text)
    await state.set_state(VacancyState.title)
    await message.answer(t(lang, "ask_position"))


@router.message(VacancyState.title)
async def vacancy_title(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(title=message.text)
    await state.set_state(VacancyState.subject)
    await message.answer(t(lang, "ask_subject"))


@router.message(VacancyState.subject)
async def vacancy_subject(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(subject=message.text)
    await state.set_state(VacancyState.requirements)
    await message.answer(t(lang, "ask_requirements"), reply_markup=get_cancel_skip_keyboard(lang))


@router.message(VacancyState.requirements)
async def vacancy_requirements(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    value = None if message.text == t(lang, "btn_skip") else message.text
    await state.update_data(requirements=value)
    await state.set_state(VacancyState.salary)
    await message.answer(t(lang, "ask_salary"), reply_markup=get_cancel_skip_keyboard(lang))


@router.message(VacancyState.salary)
async def vacancy_salary(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    value = None if message.text == t(lang, "btn_skip") else message.text
    await state.update_data(salary=value)
    await state.set_state(VacancyState.region)
    await message.answer(t(lang, "ask_region"), reply_markup=get_cancel_keyboard(lang))


@router.message(VacancyState.region)
async def vacancy_region(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(region=message.text)
    await state.set_state(VacancyState.work_format)
    await message.answer(t(lang, "ask_format"), reply_markup=get_work_format_keyboard(lang))


@router.message(VacancyState.work_format, F.text.in_(all_variants("btn_offline") + all_variants("btn_online")))
async def vacancy_work_format(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    fmt = "offline" if message.text == t(lang, "btn_offline") else "online"
    await state.update_data(work_format=fmt)
    await state.set_state(VacancyState.contact)
    await message.answer(t(lang, "ask_contact"), reply_markup=get_cancel_keyboard(lang))


@router.message(VacancyState.contact)
async def vacancy_contact(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(contact=message.text)
    data = await state.get_data()

    preview = (
        f"{t(lang, 'vacancy_preview_title')}\n\n"
        f"🏢 {data['company_name']}\n"
        f"{t(lang, 'v_position')} {data['title']}\n"
        f"{t(lang, 'v_subject')} {data['subject']}\n"
        f"{t(lang, 'v_requirements')} {data.get('requirements') or '—'}\n"
        f"{t(lang, 'v_salary')} {data.get('salary') or '—'}\n"
        f"{t(lang, 'v_region')} {data['region']}\n"
        f"{t(lang, 'v_format')} {data['work_format']}\n"
        f"{t(lang, 'v_contact')} {data['contact']}"
    )
    await state.set_state(VacancyState.confirm)
    await message.answer(preview, reply_markup=get_confirm_keyboard(lang), parse_mode="HTML")


@router.message(VacancyState.confirm, F.text.in_(all_variants("btn_confirm")))
async def vacancy_save(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    lang = data["lang"]
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
    await message.answer(t(lang, "vacancy_saved"), reply_markup=get_main_keyboard(lang))

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


@router.message(F.text.in_(all_variants("btn_post_resume")))
async def resume_start(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await state.update_data(lang=lang)
    await state.set_state(ResumeState.full_name)
    await message.answer(t(lang, "ask_full_name"), reply_markup=get_cancel_keyboard(lang))


@router.message(ResumeState.full_name)
async def resume_full_name(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(full_name=message.text)
    await state.set_state(ResumeState.phone)
    await message.answer(t(lang, "ask_phone"))


@router.message(ResumeState.phone)
async def resume_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(phone=message.text)
    await state.set_state(ResumeState.subject)
    await message.answer(t(lang, "ask_resume_subject"))


@router.message(ResumeState.subject)
async def resume_subject(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(subject=message.text)
    await state.set_state(ResumeState.experience)
    await message.answer(t(lang, "ask_experience"), reply_markup=get_cancel_skip_keyboard(lang))


@router.message(ResumeState.experience)
async def resume_experience(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    value = None if message.text == t(lang, "btn_skip") else message.text
    await state.update_data(experience=value)
    await state.set_state(ResumeState.education)
    await message.answer(t(lang, "ask_education"), reply_markup=get_cancel_keyboard(lang))


@router.message(ResumeState.education)
async def resume_education(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(education=message.text)
    await state.set_state(ResumeState.about)
    await message.answer(t(lang, "ask_about"), reply_markup=get_cancel_skip_keyboard(lang))


@router.message(ResumeState.about)
async def resume_about(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    value = None if message.text == t(lang, "btn_skip") else message.text
    await state.update_data(about=value)
    await state.set_state(ResumeState.region)
    await message.answer(t(lang, "ask_resume_region"), reply_markup=get_cancel_keyboard(lang))


@router.message(ResumeState.region)
async def resume_region(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data["lang"]
    await state.update_data(region=message.text)
    data = await state.get_data()

    preview = (
        f"{t(lang, 'resume_preview_title')}\n\n"
        f"{t(lang, 'r_name')} {data['full_name']}\n"
        f"{t(lang, 'r_phone')} {data['phone']}\n"
        f"{t(lang, 'v_subject')} {data['subject']}\n"
        f"{t(lang, 'r_experience')} {data.get('experience') or '—'}\n"
        f"{t(lang, 'r_education')} {data['education']}\n"
        f"{t(lang, 'r_about')} {data.get('about') or '—'}\n"
        f"{t(lang, 'v_region')} {data['region']}"
    )
    await state.set_state(ResumeState.confirm)
    await message.answer(preview, reply_markup=get_confirm_keyboard(lang), parse_mode="HTML")


@router.message(ResumeState.confirm, F.text.in_(all_variants("btn_confirm")))
async def resume_save(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    lang = data["lang"]
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
    await message.answer(t(lang, "resume_saved"), reply_markup=get_main_keyboard(lang))

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

    recipient_lang = await get_user_lang(recipient_id)

    await callback.message.edit_reply_markup(reply_markup=None)

    if new_status == "approved":
        await callback.message.answer(f"✅ #{item_id} tasdiqlandi.")
        try:
            await bot.send_message(recipient_id, t(recipient_lang, "approved_notify"))
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
            await bot.send_message(recipient_id, t(recipient_lang, "rejected_notify"))
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

@router.message(F.text.in_(all_variants("btn_cancel")))
async def cancel_handler(message: Message, state: FSMContext):
    lang = await get_user_lang(message.from_user.id)
    await state.clear()
    await message.answer(t(lang, "cancelled"), reply_markup=get_main_keyboard(lang))

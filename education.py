from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database import async_session, EducationProgress

router = Router()

QUESTIONS = {
    "📐 Matematika": [
        ("12 × 8 = ?", ["86", "96", "108", "88"], 1, "12×8 = 96."),
        ("3/4 ning o‘nli kasr ko‘rinishi?", ["0.25", "0.5", "0.75", "1.25"], 2, "3 ÷ 4 = 0.75."),
        ("x + 7 = 15. x = ?", ["6", "7", "8", "9"], 2, "15−7 = 8."),
        ("5² = ?", ["10", "20", "25", "15"], 2, "5×5 = 25."),
        ("100 ning 20% i nechaga teng?", ["10", "20", "25", "30"], 1, "100×0.20 = 20."),
    ],
    "🇬🇧 Ingliz tili": [
        ("'Apple' so‘zining ko‘pligi?", ["Apples", "Applees", "Appls", "Applez"], 0, "Ko‘plik shakli: apples."),
        ("I ___ a student.", ["am", "is", "are", "be"], 0, "I bilan am ishlatiladi."),
        ("'Big' so‘zining antonimi?", ["Tall", "Small", "Fast", "Long"], 1, "Big ↔ small."),
        ("Past tense: 'go' → ?", ["goed", "gone", "went", "going"], 2, "Go fe’lining past tense shakli went."),
        ("'Beautiful' nimani anglatadi?", ["Chiroyli", "Tez", "Qimmat", "Katta"], 0, "Beautiful = chiroyli."),
    ],
    "🏛 Tarix": [
        ("O‘zbekiston mustaqilligi qachon e’lon qilingan?", ["1990", "1991", "1992", "1989"], 1, "1991-yil 1-sentabr — Mustaqillik kuni."),
        ("Amir Temur qaysi asrda yashagan?", ["XIII–XIV", "XIV–XV", "XV–XVI", "XII–XIII"], 1, "Amir Temur 1336–1405-yillarda yashagan."),
        ("Qadimgi Misr yozuvi nima deb atalgan?", ["Lotin", "Kirill", "Iyeroglif", "Runik"], 2, "Qadimgi Misrda iyeroglif yozuvi ishlatilgan."),
        ("Buyuk Ipak yo‘li asosan nimani bog‘lagan?", ["Osiyo va Yevropani", "Afrika va Amerikani", "Avstraliya va Afrikani", "Faqat Xitoyni"], 0, "Savdo yo‘li Sharq va G‘arbni bog‘lagan."),
        ("O‘zbekiston poytaxti?", ["Samarqand", "Buxoro", "Toshkent", "Xiva"], 2, "O‘zbekiston poytaxti — Toshkent."),
    ],
}

LESSONS = {
    "📐 Matematika": "📐 <b>Mini dars: Foiz</b>\n\nFoiz — sonning yuzdan bir qismi. Masalan, 20% = 20/100 = 0.2.\n\n💡 250 ning 20% i: 250 × 0.2 = 50.",
    "🇬🇧 Ingliz tili": "🇬🇧 <b>Mini dars: Present Simple</b>\n\nI/You/We/They → work\nHe/She/It → works\n\n💡 Misol: She works every day.",
    "🏛 Tarix": "🏛 <b>Mini dars: Amir Temur</b>\n\nAmir Temur 1336–1405-yillarda yashagan. U Markaziy Osiyoda kuchli davlat barpo etgan va Samarqandni yirik siyosiy-madaniy markazga aylantirgan.",
}

def education_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📐 Matematika", callback_data="edu_sub_math"), InlineKeyboardButton(text="🇬🇧 Ingliz tili", callback_data="edu_sub_en")],
        [InlineKeyboardButton(text="🏛 Tarix", callback_data="edu_sub_history")],
        [InlineKeyboardButton(text="🏆 Natijam", callback_data="edu_stats"), InlineKeyboardButton(text="💡 Maslahat", callback_data="edu_tip")],
    ])

def subject_keyboard(subject):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Testni boshlash", callback_data=f"edu_quiz_{list(QUESTIONS).index(subject)}")],
        [InlineKeyboardButton(text="📖 Mini dars", callback_data=f"edu_lesson_{list(QUESTIONS).index(subject)}")],
        [InlineKeyboardButton(text="⬅️ Orqaga", callback_data="edu_home")],
    ])

async def get_progress(user_id):
    async with async_session() as session:
        p = await session.get(EducationProgress, user_id)
        if not p:
            p = EducationProgress(user_id=user_id)
            session.add(p)
            await session.commit()
            await session.refresh(p)
        return p

async def save_answer(user_id, subject, correct):
    async with async_session() as session:
        p = await session.get(EducationProgress, user_id)
        if not p:
            p = EducationProgress(user_id=user_id)
            session.add(p)
        p.total_answers += 1
        p.last_subject = subject
        if correct:
            p.correct_answers += 1
            p.points += 10
            p.streak += 1
        else:
            p.streak = 0
        await session.commit()
        return p

@router.message(F.text == "/study")
@router.message(F.text == "🎓 O‘qish")
async def study_home(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("🎓 <b>TA’LIM MARKAZI</b>\n━━━━━━━━━━━━━━\n📚 Fan tanlang yoki natijangizni ko‘ring.\n\n🧠 Test → ball to‘plang\n📖 Mini dars → tez o‘rganing\n🏆 Natija → rivojlanishingizni kuzating", parse_mode="HTML", reply_markup=education_menu())

@router.callback_query(F.data == "edu_home")
async def edu_home(call: CallbackQuery):
    await call.message.edit_text("🎓 <b>TA’LIM MARKAZI</b>\n\nFan tanlang:", parse_mode="HTML", reply_markup=education_menu())
    await call.answer()

@router.callback_query(F.data.startswith("edu_sub_"))
async def choose_subject(call: CallbackQuery):
    idx = {"math": 0, "en": 1, "history": 2}[call.data.split("_")[-1]]
    subject = list(QUESTIONS)[idx]
    await call.message.edit_text(f"{subject}\n\n📌 Nima qilamiz?", reply_markup=subject_keyboard(subject))
    await call.answer()

@router.callback_query(F.data.startswith("edu_lesson_"))
async def lesson(call: CallbackQuery):
    subject = list(QUESTIONS)[int(call.data.split("_")[-1])]
    await call.message.edit_text(LESSONS[subject], parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧠 Testni boshlash", callback_data=f"edu_quiz_{list(QUESTIONS).index(subject)}")],[InlineKeyboardButton(text="⬅️ Orqaga", callback_data="edu_home")]]))
    await call.answer()

@router.callback_query(F.data.startswith("edu_quiz_"))
async def quiz_start(call: CallbackQuery, state: FSMContext):
    subject = list(QUESTIONS)[int(call.data.split("_")[-1])]
    await state.update_data(subject=subject, q=0, score=0)
    await send_question(call, state)

async def send_question(call, state):
    data = await state.get_data()
    subject, q = data["subject"], data["q"]
    question, options, _, _ = QUESTIONS[subject][q]
    buttons = [[InlineKeyboardButton(text=f"{chr(65+i)}. {opt}", callback_data=f"edu_ans_{i}")] for i, opt in enumerate(options)]
    buttons.append([InlineKeyboardButton(text="❌ Testni tugatish", callback_data="edu_home")])
    await call.message.edit_text(f"🧠 <b>{subject}</b>\n\n<b>{q+1}/5</b>  {question}", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("edu_ans_"))
async def answer(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data.get("subject"):
        await call.answer("Test topilmadi", show_alert=True); return
    subject, q = data["subject"], data["q"]
    selected = int(call.data.split("_")[-1])
    question, options, correct_idx, explanation = QUESTIONS[subject][q]
    correct = selected == correct_idx
    score = data.get("score", 0) + (1 if correct else 0)
    await save_answer(call.from_user.id, subject, correct)
    mark = "✅ To‘g‘ri!" if correct else f"❌ Noto‘g‘ri. To‘g‘ri javob: {options[correct_idx]}"
    await call.message.edit_text(f"{mark}\n\n💡 {explanation}")
    await call.answer()
    if q == 4:
        await state.clear()
        await call.message.edit_text(f"🎉 <b>Test tugadi!</b>\n\n📚 Fan: {subject}\n🎯 Natija: <b>{score}/5</b>\n⭐ Qo‘shilgan ball: <b>{score*10}</b>\n\nYana bir test ishlang va natijangizni oshiring!", parse_mode="HTML", reply_markup=education_menu())
    else:
        await state.update_data(q=q+1, score=score)
        await call.message.edit_text(f"➡️ Keyingi savol...\n\n<b>{q+2}/5</b>", parse_mode="HTML")
        await send_question(call, state)

@router.callback_query(F.data == "edu_stats")
async def stats(call: CallbackQuery):
    p = await get_progress(call.from_user.id)
    accuracy = round((p.correct_answers / p.total_answers) * 100) if p.total_answers else 0
    await call.message.edit_text(f"🏆 <b>SIZNING NATIJANGIZ</b>\n━━━━━━━━━━━━━━\n⭐ Ball: <b>{p.points}</b>\n✅ To‘g‘ri javoblar: <b>{p.correct_answers}</b>\n📝 Jami javoblar: <b>{p.total_answers}</b>\n🎯 Aniqlik: <b>{accuracy}%</b>\n🔥 Ketma-ket to‘g‘ri: <b>{p.streak}</b>", parse_mode="HTML", reply_markup=education_menu())
    await call.answer()

@router.callback_query(F.data == "edu_tip")
async def tip(call: CallbackQuery):
    await call.message.edit_text("💡 <b>Bugungi maslahat</b>\n\n⏱ Har kuni 15–20 daqiqa test ishlang.\n🧠 Xato javobni yodlashdan ko‘ra, sababini tushuning.\n📖 Har bir testdan keyin mini darsni o‘qing.\n🔥 Ketma-ket kunlarda shug‘ullanish odatni kuchaytiradi.", parse_mode="HTML", reply_markup=education_menu())
    await call.answer()

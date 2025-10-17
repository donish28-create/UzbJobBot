import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta
from aiogram import Dispatcher, Bot
from aiogram.types import Message
from database import get_similar_posts  # бу функция базадан ўхшаш эълонларни олади деб ҳисоблаймиз

# 🔹 Эълон берилгандан кейин ўхшаш эълонларни топиш
async def show_similar_posts(bot: Bot, user_id: int, category: str, region: str):
    matches = await get_similar_posts(category, region)
    if not matches:
        await bot.send_message(user_id, "😔 Hozircha o‘xshash e’lonlar topilmadi.")
        return

    text = "🧩 Sizga o‘xshash e’lonlar:\n\n"
    for m in matches[:5]:
        text += (
            f"👤 {m['full_name']}\n"
            f"🛠 {m['category']} | {m['region']}, {m['district']}\n"
            f"💸 {m['salary']}\n"
            f"📞 {m['contact']}\n\n"
        )
    await bot.send_message(user_id, text)


# 🔹 Бу функцияни main.py дан setup_matching(dp, bot) орқали чақириш учун
def setup_matching(dp: Dispatcher, bot: Bot):
    print("🔗 Matching system initialized.")
    # Агар керак бўлса, ивентлар ёки триггерлар бу ерда уланади
    # Масалан, эълон жойланганда show_similar_posts(...) ишга тушсин
    pass

DB_PATH = "data.db"
CHANNEL_ID = "@UzJobElonlar"

# ==================== Klaviatura ====================
def kb_matching():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧩 Menga mos ishlarni ko‘rish")],
            [KeyboardButton(text="🧩 Menga mos ishchilarni ko‘rish")],
            [KeyboardButton(text="🚫 To‘xtatish")]
        ],
        resize_keyboard=True
    )

# ==================== Ish topish uchun mos e’lonlarni chiqarish ====================
async def show_matches(m: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT category FROM seekers WHERE tg_id = ? ORDER BY id DESC LIMIT 1", (m.from_user.id,)) as cur:
            seeker = await cur.fetchone()

        if not seeker:
            await m.answer("Siz hali ish yo‘nalishini tanlamagansiz.", reply_markup=ReplyKeyboardRemove())
            return

        category = seeker[0]
        async with db.execute("""
            SELECT full_name, region, salary, contact FROM offers
            WHERE category = ? ORDER BY created_at DESC LIMIT 10
        """, (category,)) as cur:
            offers = await cur.fetchall()

    if not offers:
        await m.answer("Hozircha bu yo‘nalishda yangi ish takliflari yo‘q.")
        return

    await m.answer(f"🔍 <b>{category}</b> yo‘nalishidagi eng so‘nggi ish takliflari:\n", reply_markup=kb_matching())

    for full_name, region, salary, contact in offers:
        text = (
            f"🏢 <b>{full_name}</b>\n"
            f"📍 {region}\n"
            f"💸 {salary}\n"
            f"📞 {contact}\n"
            f"— — —\n"
            f"#ishchi_kerak #{category.replace(' ', '_').lower()}"
        )
        await m.answer(text)
        await asyncio.sleep(0.4)

    await m.answer("🕒 Bunday e’lonlar sizga 2 oy davomida avtomatik yuborilib turadi ✅")

# ==================== Ish beruvchi uchun mos ishchilarni chiqarish ====================
async def show_worker_matches(m: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT category FROM employers WHERE tg_id = ? ORDER BY id DESC LIMIT 1", (m.from_user.id,)) as cur:
            employer = await cur.fetchone()

        if not employer:
            await m.answer("Siz hali ish yo‘nalishini tanlamagansiz.", reply_markup=ReplyKeyboardRemove())
            return

        category = employer[0]
        async with db.execute("""
            SELECT full_name, region, salary, contact FROM seekers
            WHERE category = ? ORDER BY created_at DESC LIMIT 10
        """, (category,)) as cur:
            seekers = await cur.fetchall()

    if not seekers:
        await m.answer("Hozircha bu yo‘nalishda yangi ishchilar yo‘q.")
        return

    await m.answer(f"👷‍♂️ <b>{category}</b> yo‘nalishidagi ishchilar ro‘yxati:\n", reply_markup=kb_matching())

    for full_name, region, salary, contact in seekers:
        text = (
            f"👤 <b>{full_name}</b>\n"
            f"📍 {region}\n"
            f"💸 {salary}\n"
            f"📞 {contact}\n"
            f"— — —\n"
            f"#ish_kerak #{category.replace(' ', '_').lower()}"
        )
        await m.answer(text)
        await asyncio.sleep(0.4)

    await m.answer("🕒 Bunday e’lonlar sizga 2 oy davomida avtomatik yuborilib turadi ✅")

# ==================== Avtomatik yuborish ====================
async def send_new_matches(bot: Bot, category: str, post_text: str, target="seekers"):
    cutoff = datetime.now() - timedelta(days=60)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(f"""
            SELECT DISTINCT tg_id FROM {target}
            WHERE category = ? AND datetime(created_at) > ?
        """, (category, cutoff.strftime("%Y-%m-%d %H:%M:%S"))) as cur:
            users = await cur.fetchall()

    for (tg_id,) in users:
        try:
            await bot.send_message(tg_id, f"🆕 Sizga mos yangi e’lon:\n\n{post_text}")
            await asyncio.sleep(0.3)
        except Exception:
            continue

# ==================== Matching’ni o‘chirish ====================
async def stop_matching(m: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM seekers WHERE tg_id = ?", (m.from_user.id,))
        await db.execute("DELETE FROM employers WHERE tg_id = ?", (m.from_user.id,))
        await db.commit()
    await m.answer("🚫 Mos e’lonlarni yuborish to‘xtatildi.", reply_markup=ReplyKeyboardRemove())

# ==================== Dispatcher bilan bog‘lash ====================
def setup_matching(dp: Dispatcher, bot: Bot):
    @dp.message(F.text == "🧩 Menga mos ishlarni ko‘rish")
    async def _(m: Message):
        await show_matches(m)

    @dp.message(F.text == "🧩 Menga mos ishchilarni ko‘rish")
    async def _(m: Message):
        await show_worker_matches(m)

    @dp.message(F.text == "🚫 To‘xtatish")
    async def _(m: Message):
        await stop_matching(m)

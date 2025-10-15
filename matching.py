import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from datetime import datetime, timedelta
from database import db_init

DB_PATH = "data.db"
CHANNEL_ID = "@UzJobElonlar"

# ==================== Klaviatura ====================
def kb_matching():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧩 Menga mos ishlarni ko‘rish")],
            [KeyboardButton(text="🚫 To‘xtatish")]
        ],
        resize_keyboard=True
    )

# ==================== Mos ishlarni chiqarish ====================
async def show_matches(m: Message):
    async with aiosqlite.connect(DB_PATH) as db:
        # Foydalanuvchi qaysi yo‘nalishda ish qidirganini topamiz
        async with db.execute("SELECT category FROM seekers WHERE tg_id = ? ORDER BY id DESC LIMIT 1", (m.from_user.id,)) as cur:
            seeker = await cur.fetchone()

        if not seeker:
            await m.answer("Siz hali ish yo‘nalishini tanlamagansiz.", reply_markup=ReplyKeyboardRemove())
            return

        category = seeker[0]
        # Shu yo‘nalish bo‘yicha oxirgi 10 ta taklifni chiqaramiz
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

# ==================== Avtomatik yuborish ====================
async def send_new_matches(bot: Bot, category: str, post_text: str):
    cutoff = datetime.now() - timedelta(days=60)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("""
            SELECT DISTINCT tg_id FROM seekers
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
        await db.commit()
    await m.answer("🚫 Mos e’lonlarni yuborish to‘xtatildi.", reply_markup=ReplyKeyboardRemove())

# ==================== Ulanish funksiyasi ====================
def setup_matching(dp: Dispatcher, bot: Bot):
    @dp.message(F.text == "🧩 Menga mos ishlarni ko‘rish")
    async def _(m: Message):
        await show_matches(m)

    @dp.message(F.text == "🚫 To‘xtatish")
    async def _(m: Message):
        await stop_matching(m)

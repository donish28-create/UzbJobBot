import asyncio
import aiosqlite
import os
import re
from typing import List, Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# -------------------- Env --------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
CHANNEL_ID = os.getenv("CHANNEL_ID", "@uzjobelonlar")

if BOT_TOKEN in ("", "REPLACE", None):
    raise SystemExit("Please set BOT_TOKEN in environment or .env")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()
DB_PATH = "data.db"

# -------------------- Ma'lumotlar --------------------
CATEGORIES = [
    "Qurilish / Usta","Haydovchi / Avto","Oshpaz / Kafe / Restoran","Sotuv / Kassir / Admin",
    "Tikuvchi / Atelye / Moda","Yordamchi ishchi","O‘qituvchi / Repetitor","Tibbiyot / Parvarish",
    "Uy xizmatchisi / Tozalash","IT / Dasturchi / Dizayn / SMM","Sklad / Qadoqlash / Logistika",
    "Call center / Operator","Ofis / Buxgalteriya / Menejer","Elektrik / Santexnik / Ta’mirlash",
    "Qishloq xo‘jaligi / Dehqonchilik","Enaga / Bola parvarishi","Model / Promo / Reklama",
    "Kontent yaratuvchi / Bloger yordamchisi","Talabalar uchun vaqtinchalik","Go‘zallik saloni",
    "Yetkazib berish / Kuryer","Fermerlik / Chorvachilik","Laborant / Texnik xodim","Avtoservis / Usta"
]

REGIONS = {
    "Toshkent shahri": ["Chilonzor", "Yakkasaroy", "Yunusobod", "Sergeli", "Yashnobod"],
    "Andijon": ["Asaka", "Xo‘jaobod", "Paxtaobod", "Andijon sh."],
    "Farg‘ona": ["Marg‘ilon", "Qo‘qon", "Beshariq", "Oltiariq"],
    "Namangan": ["Chust", "Pop", "Uchqo‘rg‘on", "Namangan sh."],
    "Samarqand": ["Urgut", "Kattaqo‘rg‘on", "Bulung‘ur"],
    "Buxoro": ["G‘ijduvon", "Olot", "Vobkent"],
    "Xorazm": ["Urganch", "Xiva", "Gurlan"],
    "Qashqadaryo": ["Shahrisabz", "Kitob", "Qarshi"],
    "Surxondaryo": ["Denov", "Sherobod", "Termiz"],
    "Jizzax": ["G‘allaorol", "Do‘stlik", "Jizzax sh."],
    "Sirdaryo": ["Guliston", "Yangiyer", "Sardoba"],
    "Navoiy": ["Zarafshon", "Konimex", "Navoiy sh."],
    "Qoraqalpog‘iston R.": ["Nukus", "Taxiatosh", "Beruniy"],
    "Toshkent viloyati": ["Angren", "Bekobod", "Ohangaron", "Chirchiq"],
    "Butun Oʻzbekiston boʻyicha": []
}

# -------------------- Klaviaturalar --------------------
def rows(items, n=2):
    return [ [KeyboardButton(text=i) for i in items[x:x+n]] for x in range(0, len(items), n) ]

def kb_main():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👤 Ish kerak")],[KeyboardButton(text="🏭 Ishchi kerak")]],
        resize_keyboard=True
    )

def kb_categories():
    keyboard = rows(CATEGORIES, 2)
    keyboard.append([KeyboardButton(text="➕ Boshqa yo‘nalish")])
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_regions():
    k = rows(list(REGIONS.keys()), 2)
    k.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=k, resize_keyboard=True)

def kb_districts(region):
    items = REGIONS.get(region, [])
    if not items:
        return ReplyKeyboardRemove()
    k = rows(items, 2)
    k.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=k, resize_keyboard=True)

def kb_contact():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )

# -------------------- FSM --------------------
class Seeker(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    district = State()
    experience = State()
    salary = State()
    contact = State()
    info = State()

class Employer(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    district = State()
    headcount = State()
    salary = State()
    contact = State()
    info = State()

# -------------------- DB --------------------
SQL_SEEKERS = """
CREATE TABLE IF NOT EXISTS seekers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER,
    full_name TEXT,
    category TEXT,
    region TEXT,
    district TEXT,
    experience TEXT,
    salary TEXT,
    contact TEXT,
    info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

SQL_OFFERS = """
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER,
    full_name TEXT,
    category TEXT,
    region TEXT,
    district TEXT,
    headcount TEXT,
    salary TEXT,
    contact TEXT,
    info TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(SQL_SEEKERS)
        await db.execute(SQL_OFFERS)
        await db.commit()

# -------------------- Helper --------------------
def clean_text(t):
    return re.sub(r"[^\w\s\.,!?()-]", "", t)[:300]

# -------------------- Handlers --------------------
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Assalomu alaykum! Bu <b>UzbJobBot</b>.\nSizga qanday yordam bera olaman?", reply_markup=kb_main())

@router.message(F.text == "⬅️ Orqaga")
async def back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Asosiy menyu:", reply_markup=kb_main())

# --- Seeker flow ---
@router.message(F.text == "👤 Ish kerak")
async def s_fullname(m: Message, state: FSMContext):
    await state.set_state(Seeker.full_name)
    await m.answer("👤 Ism familiyangizни киритинг:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.full_name, F.text)
async def s_category(m: Message, state: FSMContext):
    await state.update_data(full_name=clean_text(m.text))
    await state.set_state(Seeker.category)
    await m.answer("Qaysi yo‘nalishda ish qidiryapsiz?", reply_markup=kb_categories())

@router.message(Seeker.category, F.text == "➕ Boshqa yo‘nalish")
async def s_custom(m: Message, state: FSMContext):
    await state.set_state(Seeker.custom_category)
    await m.answer("Yo‘nalishni ёзинг:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.custom_category, F.text)
async def s_custom_done(m: Message, state: FSMContext):
    await state.update_data(category=clean_text(m.text))
    await state.set_state(Seeker.region)
    await m.answer(f"Yo‘nalish: <b>{clean_text(m.text)}</b>\nHududni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.category)
async def s_region(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Seeker.region)
    await m.answer("Hududни танланг:", reply_markup=kb_regions())

@router.message(Seeker.region)
async def s_district(m: Message, state: FSMContext):
    await state.update_data(region=m.text)
    await state.set_state(Seeker.district)
    await m.answer("Туманни танланг:", reply_markup=kb_districts(m.text))

@router.message(Seeker.district)
async def s_exp(m: Message, state: FSMContext):
    await state.update_data(district=m.text)
    await state.set_state(Seeker.experience)
    await m.answer("🧰 Tajribangiz (yil):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.experience, F.text)
async def s_salary(m: Message, state: FSMContext):
    await state.update_data(experience=clean_text(m.text))
    await state.set_state(Seeker.salary)
    await m.answer("💸 Qancha oylik kutyapsiz?:")

@router.message(Seeker.salary, F.text)
async def s_contact(m: Message, state: FSMContext):
    await state.update_data(salary=clean_text(m.text))
    await state.set_state(Seeker.contact)
    await m.answer("📞 Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Seeker.contact, F.contact)
async def s_info(m: Message, state: FSMContext):
    await state.update_data(contact=m.contact.phone_number)
    await state.set_state(Seeker.info)
    await m.answer("✏️ Qo‘shimcha ma’lumot (300 belgigacha):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.contact, F.text)
async def s_info_txt(m: Message, state: FSMContext):
    await state.update_data(contact=m.text)
    await state.set_state(Seeker.info)
    await m.answer("✏️ Qo‘shimcha ma’lumot (300 belgigacha):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.info, F.text)
async def s_done(m: Message, state: FSMContext):
    data = await state.get_data()
    data["info"] = clean_text(m.text)

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO seekers (tg_id, full_name, category, region, district, experience, salary, contact, info)
            VALUES (?,?,?,?,?,?,?,?,?)
        """, (m.from_user.id, data["full_name"], data["category"], data["region"], data["district"], data["experience"], data["salary"], data["contact"], data["info"]))
        await db.commit()

    post = (
        f"🆕 <b>Ish qidiruvchi</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"🛠 Yo‘nalish: <b>{data['category']}</b>\n"
        f"📍 Hudud: {data['region']}, {data['district']}\n"
        f"🧰 Tajriba: {data['experience']}\n"
        f"💸 Maosh kutyapti: {data['salary']}\n"
        f"📞 Aloqa: {data['contact']}\n"
        f"📝 Qo‘shimcha: {data['info']}\n\n"
        f"@UzbJobBot orqali e'lon bering 📢"
    )
    await bot.send_message(CHANNEL_ID, post)
    await m.answer("🫡 Ma'lumot @UzJobElonlar kanaliga joylandi ✅", reply_markup=kb_main())
    await state.clear()

# (Employer flow – худди шундай принципда, агар хоҳласанг кейинги босқичда қўшамиз)

# -------------------- Runner --------------------
async def main():
    dp.include_router(router)
    await db_init()
    print("✅ Bot started (worker mode)")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

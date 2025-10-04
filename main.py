import asyncio
import aiosqlite
import os
import re
from typing import List, Dict
from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# 🔹 Environment
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
CHANNEL_ID = os.getenv("CHANNEL_ID")

if not BOT_TOKEN or BOT_TOKEN == "REPLACE":
    raise SystemExit("❌ Please set BOT_TOKEN in .env")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()

DB_PATH = "data.db"

# 🔹 Yo‘nalishlar
CATEGORIES = [
    "Qurilish / Usta","Haydovchi / Avto","Oshpaz / Kafe / Restoran","Sotuv / Kassir / Admin",
    "Tikuvchi / Atelye / Moda","Yordamchi ishchi","O‘qituvchi / Repetitor","Tibbiyot / Parvarish",
    "Uy xizmatchisi / Tozalash","IT / Dasturchi / Dizayn / SMM","Sklad / Qadoqlash / Logistika",
    "Call center / Operator","Ofis / Buxgalteriya / Menejer","Elektrik / Santexnik / Ta’mirlash",
    "Qishloq xo‘jaligi / Dehqonchilik","Enaga / Bola parvarishi","Model / Promo / Reklama",
    "Kontent yaratuvchi / Bloger yordamchisi","Talabalar uchun vaqtinchalik","Go‘zallik saloni",
    "Yetkazib berish / Kuryer","Fermerlik / Chorvachilik","Laborant / Texnik xodim","Avtoservis / Usta"
]

CATEGORY_BUTTON_ROWS = [
    ["Qurilish / Usta","Haydovchi / Avto"],
    ["Oshpaz / Kafe / Restoran","Sotuv / Kassir / Admin"],
    ["Tikuvchi / Atelye / Moda","Yordamchi ishchi"],
    ["O‘qituvchi / Repetitor","Tibbiyot / Parvarish"],
    ["Uy xizmatchisi / Tozalash","IT / Dasturchi / Dizayn / SMM"],
    ["Sklad / Qadoqlash / Logistika","Call center / Operator"],
    ["Ofis / Buxgalteriya / Menejer","Elektrik / Santexnik / Ta’mirlash"],
    ["Qishloq xo‘jaligi / Dehqonchilik","Enaga / Bola parvarishi"],
    ["Model / Promo / Reklama","Kontent yaratuvchi / Bloger yordamchisi"],
    ["Talabalar uchun vaqtinchalik","Go‘zallik saloni"],
    ["Yetkazib berish / Kuryer","Fermerlik / Chorvachilik"],
    ["Laborant / Texnik xodim","Avtoservis / Usta"]
]

REGIONS = [
    "Butun Oʻzbekiston boʻyicha","Toshkent shahri","Toshkent viloyati","Andijon","Fargʻona","Namangan",
    "Samarqand","Buxoro","Xorazm","Qashqadaryo","Surxondaryo","Jizzax","Sirdaryo","Navoiy","Qoraqalpogʻiston R."
]

# 🔹 Klaviатуралар
def rows(items, n=2):
    out, r = [], []
    for i, x in enumerate(items, 1):
        r.append(KeyboardButton(text=x))
        if i % n == 0: out.append(r); r = []
    if r: out.append(r)
    return out

def kb_main():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Ish kerak")],
            [KeyboardButton(text="🏭 Ishchi kerak")]
        ],
        resize_keyboard=True
    )

def kb_categories():
    keyboard = [[KeyboardButton(text=a), KeyboardButton(text=b)] for a, b in CATEGORY_BUTTON_ROWS]
    keyboard.append([KeyboardButton(text="➕ Boshqa yo‘nalish")])
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_regions():
    k = rows(REGIONS, 2)
    k.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=k, resize_keyboard=True)

def kb_contact():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )

# 🔹 States
class Seeker(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    salary = State()
    contact = State()

class Employer(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    salary = State()
    contact = State()
    headcount = State()

# 🔹 DB
SQL_SEEKERS = """
CREATE TABLE IF NOT EXISTS seekers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER,
    full_name TEXT,
    category TEXT,
    region TEXT,
    salary TEXT,
    contact TEXT,
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
    headcount TEXT,
    salary TEXT,
    contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute(SQL_SEEKERS)
        await db.execute(SQL_OFFERS)
        await db.commit()

# 🔹 Start
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Assalomu alaykum! Bu <b>UzbJobBot</b>.\nSizga qanday yordam bera olaman?", reply_markup=kb_main())

@router.message(F.text == "⬅️ Orqaga")
async def back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Asosiy menyu:", reply_markup=kb_main())

# 👤 Ish kerak
@router.message(F.text == "👤 Ish kerak")
async def seeker_begin(m: Message, state: FSMContext):
    await state.set_state(Seeker.full_name)
    await m.answer("Ism familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.full_name)
async def seeker_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text)
    await state.set_state(Seeker.category)
    await m.answer("Qaysi yo‘nalishda ish qidiryapsiz?", reply_markup=kb_categories())

@router.message(Seeker.category, F.text == "➕ Boshqa yo‘nalish")
async def seeker_custom(m: Message, state: FSMContext):
    await state.set_state(Seeker.custom_category)
    await m.answer("Yo‘nalishni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.custom_category)
async def seeker_custom_save(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Seeker.region)
    await m.answer("Hududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.category)
async def seeker_cat(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Seeker.region)
    await m.answer("Hududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.region)
async def seeker_region(m: Message, state: FSMContext):
    await state.update_data(region=m.text)
    await state.set_state(Seeker.salary)
    await m.answer("Qancha oylik kutyapsiz? (so‘mda yoki $):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.salary)
async def seeker_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text)
    await state.set_state(Seeker.contact)
    await m.answer("Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Seeker.contact)
async def seeker_finish(m: Message, state: FSMContext):
    contact = m.contact.phone_number if m.contact else m.text
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO seekers (tg_id, full_name, category, region, salary, contact) VALUES (?,?,?,?,?,?)",
                         (m.from_user.id, data['full_name'], data['category'], data['region'], data['salary'], contact))
        await db.commit()

    post = (f"🆕 <b>Ish qidiruvchi</b>\n\n"
            f"👤 {data['full_name']}\n"
            f"🛠 Yo‘nalish: <b>{data['category']}</b>\n"
            f"📍 Hudud: {data['region']}\n"
            f"💸 Maosh kutyapti: {data['salary']}\n"
            f"📞 Aloqa: {contact}\n— — —\n"
            f"#ish_kerak #{re.sub(r'[^a-zA-Z0-9]+','_', data['category'].lower())}")

    if CHANNEL_ID:
        await bot.send_message(CHANNEL_ID, post)
    await m.answer("✅ Rahmat! E'loningiz kanalda joylashtirildi.", reply_markup=kb_main())
    await state.clear()

# 🏭 Ishчи kerak
@router.message(F.text == "🏭 Ishчи kerak")
async def emp_begin(m: Message, state: FSMContext):
    await state.set_state(Employer.full_name)
    await m.answer("Ism familiyangizни yozинг:", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.full_name)
async def emp_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text)
    await state.set_state(Employer.category)
    await m.answer("Qaysi yo‘nalishda ишчи керак?", reply_markup=kb_categories())

@router.message(Employer.category)
async def emp_category(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Employer.region)
    await m.answer("Hududни танланг:", reply_markup=kb_regions())

@router.message(Employer.region)
async def emp_region(m: Message, state: FSMContext):
    await state.update_data(region=m.text)
    await state.set_state(Employer.headcount)
    await m.answer("Nechta ishчи керак? (сон):", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.headcount)
async def emp_head(m: Message, state: FSMContext):
    await state.update_data(headcount=m.text)
    await state.set_state(Employer.salary)
    await m.answer("Qанча ойлик/таклиф қиласиз?:")

@router.message(Employer.salary)
async def emp_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text)
    await state.set_state(Employer.contact)
    await m.answer("Aloqa рақамингизни юбoринг:", reply_markup=kb_contact())

@router.message(Employer.contact)
async def emp_finish(m: Message, state: FSMContext):
    contact = m.contact.phone_number if m.contact else m.text
    data = await state.get_data()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO offers (tg_id, full_name, category, region, headcount, salary, contact) VALUES (?,?,?,?,?,?,?)",
                         (m.from_user.id, data['full_name'], data['category'], data['region'], data['headcount'], data['salary'], contact))
        await db.commit()

    post = (f"🆕 <b>Ish taklifi</b>\n\n"
            f"👤 {data['full_name']}\n"
            f"🛠 Yo‘налиш: <b>{data['category']}</b>\n"
            f"📍 Hudud: {data['region']}\n"
            f"👥 Kerak: {data['headcount']} nafar\n"
            f"💸 Taklif: {data['salary']}\n"
            f"📞 Aloqa: {contact}\n— — —\n"
            f"#ishchi_kerak #{re.sub(r'[^a-zA-Z0-9]+','_', data['category'].lower())}")

    if CHANNEL_ID:
        await bot.send_message(CHANNEL_ID, post)
    await m.answer("✅ Rahmat! E'лон каналда жойлаштирилди.", reply_markup=kb_main())
    await state.clear()

# 🔹 Runner
async def main():
    dp.include_router(router)
    await db_init()
    print("✅ Bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

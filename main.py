import asyncio
import aiosqlite
import os
import re
import aiohttp
from typing import List, Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# -------------------- Env --------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
CHANNEL_ID = os.getenv("CHANNEL_ID")

if BOT_TOKEN in ("", "REPLACE", None):
    raise SystemExit("Please set BOT_TOKEN in environment or .env")

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()

DB_PATH = "data.db"

# -------------------- Ma'lumotlar --------------------
CATEGORIES: List[str] = [
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
    ["Laborant / Texnik xodim","Avtoservis / Usta"],
]

REGIONS = [
    "Butun Oʻzbekiston boʻyicha","Toshkent shahri","Toshkent viloyati","Andijon","Fargʻona","Namangan",
    "Samarqand","Buxoro","Xorazm","Qashqadaryo","Surxondaryo","Jizzax","Sirdaryo","Navoiy","Qoraqalpogʻiston R."
]

# -------------------- Klaviaturalar --------------------
def rows(items, n=2):
    out=[]; r=[]
    for i,x in enumerate(items,1):
        r.append(KeyboardButton(text=x))
        if i%n==0: out.append(r); r=[]
    if r: out.append(r)
    return out

def kb_main():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👤 Ish kerak")],[KeyboardButton(text="🏭 Ishchi kerak")]],
        resize_keyboard=True
    )

def kb_categories():
    keyboard=[]
    for a,b in CATEGORY_BUTTON_ROWS:
        keyboard.append([KeyboardButton(text=a), KeyboardButton(text=b)])
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

# -------------------- FSM --------------------
class Seeker(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    experience = State()
    salary = State()
    contact = State()

# -------------------- DB --------------------
SQL_SEEKERS = """
CREATE TABLE IF NOT EXISTS seekers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER,
    full_name TEXT,
    category TEXT,
    region TEXT,
    experience TEXT,
    salary TEXT,
    contact TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute(SQL_SEEKERS)
        await db.commit()

# -------------------- Handlers --------------------
@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Assalomu alaykum! Bu <b>UzbJobBot</b>.\nSizga qanday yordam bera olaman?", reply_markup=kb_main())

@router.message(F.text == "⬅️ Orqaga")
async def back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Asosiy menyu:", reply_markup=kb_main())

# --- Seeker flow
@router.message(F.text == "👤 Ish kerak")
async def seeker_begin(m: Message, state: FSMContext):
    await state.set_state(Seeker.full_name)
    await m.answer("Ism familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.full_name, F.text)
async def seeker_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text.strip())
    await state.set_state(Seeker.category)
    await m.answer("Qaysi yo‘nalishda ish qidiryapsiz?", reply_markup=kb_categories())

@router.message(Seeker.category, F.text == "➕ Boshqa yo‘nalish")
async def seeker_custom_prompt(m: Message, state: FSMContext):
    await state.set_state(Seeker.custom_category)
    await m.answer("Yo‘nalishni yozib yuboring:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.custom_category, F.text)
async def seeker_custom_save(m: Message, state: FSMContext):
    await state.update_data(category=m.text.strip())
    await state.set_state(Seeker.region)
    await m.answer(f"Yo‘nalish: <b>{m.text.strip()}</b>\nHududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.category, F.text.in_([b for row in CATEGORY_BUTTON_ROWS for b in row]))
async def seeker_category(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Seeker.region)
    await m.answer("Hududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.region, F.text.in_(REGIONS))
async def seeker_region(m: Message, state: FSMContext):
    await state.update_data(region=m.text)
    await state.set_state(Seeker.experience)
    await m.answer("Tajribangiz (yil):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.experience, F.text)
async def seeker_exp(m: Message, state: FSMContext):
    await state.update_data(experience=m.text.strip())
    await state.set_state(Seeker.salary)
    await m.answer("Qancha oylik kutyapsiz? (so‘mda yoki $):")

@router.message(Seeker.salary, F.text)
async def seeker_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text.strip())
    await state.set_state(Seeker.contact)
    await m.answer("Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Seeker.contact, F.contact | F.text)
async def seeker_finish(m: Message, state: FSMContext):
    contact = m.contact.phone_number if m.contact else m.text.strip()
    data = await state.get_data()
    full_name = data["full_name"]
    category = data["category"]
    region = data["region"]
    experience = data["experience"]
    salary = data["salary"]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO seekers (tg_id, full_name, category, region, experience, salary, contact)
               VALUES (?,?,?,?,?,?,?)""",
            (m.from_user.id, full_name, category, region, experience, salary, contact)
        )
        await db.commit()

    post = (
        f"🆕 <b>Ish qidiruvchi</b>\n\n"
        f"👤 {full_name}\n"
        f"🛠 Yo‘nalish: <b>{category}</b>\n"
        f"📍 Hudud: {region}\n"
        f"🧰 Tajriba: {experience}\n"
        f"💸 Maosh kutyapti: {salary}\n"
        f"📞 Aloqa: {contact}\n"
        f"— — —\n"
        f"#ish_kerak #{re.sub(r'[^a-zA-Z0-9]+','_', category.lower())}\n\n"
        f"📝 E’lon berish: @UzbJobBot"
    )

    if CHANNEL_ID:
        try:
            await bot.send_message(CHANNEL_ID, post)
        except Exception as e:
            await m.answer(f"⚠️ E'lon kanalda chiqolmadi: {e}")

    await m.answer("🫡 Ma'lumot @UzJobElonlar kanaliga joylandi ✅", reply_markup=kb_main())
    await state.clear()

# -------------------- Keep alive --------------------
async def ping_server():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://uzbjobbot.onrender.com") as resp:
                    print(f"Pinged server: {resp.status}")
        except Exception as e:
            print(f"Ping error: {e}")
        await asyncio.sleep(60)

# -------------------- Runner --------------------
async def main():
    dp.include_router(router)
    await db_init()
    asyncio.create_task(ping_server())
    print("✅ Bot started (worker mode).")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

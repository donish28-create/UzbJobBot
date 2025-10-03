import asyncio
import aiohttp
import aiosqlite
import os
import re
from typing import List, Dict
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# 🌿 ENV yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

if BOT_TOKEN in ("", "REPLACE", None):
    raise SystemExit("Please set BOT_TOKEN in environment or .env")

# 🧠 BOT sozlamalari
bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
router = Router()
DB_PATH = "data.db"

# 🔁 Ping funksiyasi (Render "uxlab qolmasligi" uchun)
async def ping_server():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://uzbjobbot.onrender.com/") as response:
                    print("✅ Pinged server:", response.status)
        except Exception as e:
            print("⚠️ Ping failed:", e)
        await asyncio.sleep(300)  # har 5 daqiqa

# 📋 Kategoriyalar
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

CATEGORY_SYNONYMS: Dict[str, List[str]] = {
    "Haydovchi / Avto": ["haydovchi","driver","gazel","yuk mashinasi","taksi","kuryer","dastavka"],
    "Qurilish / Usta": ["usta","qurilish","santexnik","monter","suvag","shpaklyovka"],
    "Oshpaz / Kafe / Restoran": ["oshpaz","povar","ofitsiant","kafe","restoran"],
    "IT / Dasturchi / Dizayn / SMM": ["programmist","developer","dasturchi","smm","grafik","dizayn","frontend","backend"],
    "Tikuvchi / Atelye / Moda": ["tikuvchi","atele","tikish","moda"],
    "Uy xizmatchisi / Tozalash": ["uy xizmatchisi","farrosh","tozalash"],
    "Sotuv / Kassir / Admin": ["sotuvchi","kassir","administrator","admin"],
    "Ofis / Buxgalteriya / Menejer": ["buxgalter","menedjer","ofis"],
    "Elektrik / Santexnik / Ta’mirlash": ["elektrik","santexnik","tamirlash","ta'mirlash"],
    "Yetkazib berish / Kuryer": ["kuryer","yetkazib berish","dostavka"],
    "Yordamchi ishchi": ["raznorabochiy","yordamchi"],
}

REGIONS = [
    "Butun Oʻzbekiston boʻyicha","Toshkent shahri","Toshkent viloyati","Andijon","Fargʻona","Namangan",
    "Samarqand","Buxoro","Xorazm","Qashqadaryo","Surxondaryo","Jizzax","Sirdaryo","Navoiy","Qoraqalpogʻiston R."
]

# 🔘 Klaviatura funksiyalari
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

def kb_visibility():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Raqam ko‘rinsin"), KeyboardButton(text="❌ Raqam ko‘rinmasin")]],
        resize_keyboard=True
    )

# 🔹 State-lar (FSM)
class Seeker(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    experience = State()
    salary = State()
    contact = State()
    contact_visible = State()

class Employer(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    headcount = State()
    salary = State()
    contact = State()
    contact_visible = State()

# 🧱 Ma’lumotlar bazasi
INIT_SQL = """
CREATE TABLE IF NOT EXISTS seekers (...);
CREATE TABLE IF NOT EXISTS offers (...);
CREATE TABLE IF NOT EXISTS counters (...);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(INIT_SQL)
        for c in CATEGORIES:
            await db.execute("INSERT OR IGNORE INTO counters (category, seekers_count, offers_count) VALUES (?,0,0)", (c,))
        await db.commit()

# 🚀 Bot ishga tushuruvchi asosiy funksiya
async def main():
    dp.include_router(router)
    asyncio.create_task(ping_server())  # 🔹 Ping fon rejimida ishga tushadi
    await db_init()  # 🔹 Baza yaratiladi
    await dp.start_polling(bot)  # 🔹 Bot ishga tushadi

if __name__ == "__main__":
    asyncio.run(main())

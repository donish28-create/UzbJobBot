import asyncio
import aiosqlite
import os
import re
from typing import List, Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    ReplyKeyboardRemove
)
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
    ["Laborant / Texnik xodim","Avtoservis / Usta"],
]

# ✅ Вилоятлар ва уларнинг туманлари
REGIONS = {
    "Toshkent shahri": ["Chilonzor", "Yunusobod", "Sergeli", "Yakkasaroy", "Shayxontohur", "Mirzo Ulug‘bek", "Uchtepa", "Olmazor"],
    "Andijon": ["Andijon shahar", "Asaka", "Baliqchi", "Bo‘z", "Buloqboshi", "Izboskan", "Jalaquduq", "Qo‘rg‘ontepa", "Marhamat", "Oltinko‘l", "Paxtaobod", "Shahrixon", "Ulug‘nor", "Xonobod"],
    "Farg‘ona": ["Farg‘ona shahar", "Bag‘dod", "Beshariq", "Dang‘ara", "Furqat", "Oltiariq", "Qo‘qon", "Quva", "Quvasoy", "Rishton", "So‘x", "Toshloq", "Uchko‘prik", "Yozyovon"],
    "Namangan": ["Namangan shahar", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin", "Pop", "To‘raqo‘rg‘on", "Uychi", "Uchqo‘rg‘on", "Yangiqo‘rg‘on"],
    "Samarqand": ["Samarqand shahar", "Bulung‘ur", "Ishtixon", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Nurobod", "Oqdaryo", "Pastdarg‘om", "Paxtachi", "Payariq", "Qo‘shrabot", "Toyloq", "Urgut"],
}

# -------------------- Klaviатуралар --------------------
def rows(items, n=2):
    out=[]; r=[]
    for i,x in enumerate(items,1):
        r.append(KeyboardButton(text=x))
        if i%n==0: out.append(r); r=[]
    if r: out.append(r)
    return out

def kb_main():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👤 Ish kerak")],
                  [KeyboardButton(text="🏭 Ishchi kerak")]],
        resize_keyboard=True
    )

def kb_categories():
    keyboard = [ [KeyboardButton(text=a), KeyboardButton(text=b)] for a,b in CATEGORY_BUTTON_ROWS ]
    keyboard.append([KeyboardButton(text="➕ Boshqa yo‘nalish")])
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_regions():
    k = rows(list(REGIONS.keys()), 2)
    k.insert(0, [KeyboardButton(text="Butun Oʻzbekiston boʻyicha")])
    k.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=k, resize_keyboard=True)

def kb_districts(region):
    districts = REGIONS.get(region, [])
    k = rows(districts, 2)
    k.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=k, resize_keyboard=True)

def kb_contact():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)]],
        resize_keyboard=True
    )

# -------------------- FSM States --------------------
class Seeker(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    district = State()
    experience = State()
    salary = State()
    contact = State()
    extra = State()

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
    extra TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute(SQL_SEEKERS)
        await db.commit()

# -------------------- Helper --------------------
async def check_subscription(user_id):
    if not CHANNEL_ID: return True
    try:
        chat_member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# -------------------- Handlers --------------------
@router.message(CommandStart())
async def start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Assalomu alaykum! Bu <b>UzbJobBot</b>.\nSizga qanday yordam bera olaman?", reply_markup=kb_main())

@router.message(F.text == "👤 Ish kerak")
async def seeker_start(m: Message, state: FSMContext):
    sub = await check_subscription(m.from_user.id)
    if not sub:
        return await m.answer("⚠️ Iltimos, avval kanalga a'zo bo‘ling:\n👉 {}".format(CHANNEL_ID))
    await state.set_state(Seeker.full_name)
    await m.answer("Ism familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.full_name)
async def seeker_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text.strip())
    await state.set_state(Seeker.category)
    await m.answer("Qaysi yo‘nalishda ish qidiryapsiz?", reply_markup=kb_categories())

@router.message(Seeker.category)
async def seeker_category(m: Message, state: FSMContext):
    category = m.text.strip()
    if category not in [b for r in CATEGORY_BUTTON_ROWS for b in r] and category != "➕ Boshqa yo‘nalish":
        return await m.answer("Iltimos, yo‘nalishni tugmalardan tanlang.")
    if category == "➕ Boshqa yo‘nalish":
        await state.set_state(Seeker.custom_category)
        return await m.answer("Yo‘nalishni yozing:", reply_markup=ReplyKeyboardRemove())
    await state.update_data(category=category)
    await state.set_state(Seeker.region)
    await m.answer("Hududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.custom_category)
async def seeker_custom(m: Message, state: FSMContext):
    await state.update_data(category=m.text.strip())
    await state.set_state(Seeker.region)
    await m.answer(f"Yo‘nalish: <b>{m.text}</b>\nHududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.region)
async def seeker_region(m: Message, state: FSMContext):
    region = m.text
    if region not in REGIONS and region != "Butun Oʻzbekiston boʻyicha":
        return await m.answer("Iltimos, viloyatni tanланг.")
    await state.update_data(region=region)
    if region != "Butun Oʻzbekiston boʻyicha":
        await state.set_state(Seeker.district)
        return await m.answer("Tumanni tanlang:", reply_markup=kb_districts(region))
    await state.update_data(district="-")
    await state.set_state(Seeker.experience)
    await m.answer("Tajribangiz (yil):", reply_markup=ReplyKeyboardRemove())
@router.message(Seeker.experience)
async def seeker_experience(m: Message, state: FSMContext):
    await state.update_data(experience=m.text.strip())
    await state.set_state(Seeker.salary)
    await m.answer("Qancha oylik kutyapsiz? (so‘mda yoki $):")

@router.message(Seeker.salary)
async def seeker_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text.strip())
    await state.set_state(Seeker.contact)
    await m.answer("Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Seeker.contact, F.contact)
async def seeker_contact(m: Message, state: FSMContext):
    await state.update_data(contact=m.contact.phone_number)
    await state.set_state(Seeker.extra)
    await m.answer("Qo‘shimcha ma'lumot (300 ta belgigacha):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.contact, F.text)
async def seeker_contact_text(m: Message, state: FSMContext):
    await state.update_data(contact=m.text.strip())
    await state.set_state(Seeker.extra)
    await m.answer("Qo‘shimcha ma'lumot (300 ta belgigacha):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.extra)
async def seeker_extra(m: Message, state: FSMContext):
    text = m.text.strip()
    if len(text) > 300:
        return await m.answer(f"⚠️ Matn juda uzun! {len(text)} ta belgi bor. Iltimos 300 tadan oshmasin.")
    await state.update_data(extra=text)
    data = await state.get_data()

    full_name = data["full_name"]
    category = data["category"]
    region = data["region"]
    district = data.get("district", "-")
    experience = data["experience"]
    salary = data["salary"]
    contact = data["contact"]
    extra = data["extra"]

    post = (
        f"🆕 <b>Ish qidiruvchi</b>\n\n"
        f"👤 {full_name}\n"
        f"🛠 Yo‘nalish: <b>{category}</b>\n"
        f"📍 Hudud: {region}, {district}\n"
        f"🧰 Tajriba: {experience}\n"
        f"💸 Maosh: {salary}\n"
        f"📞 Aloqa: {contact}\n"
        f"📋 Qo‘shimcha: {extra or '-'}\n"
        f"— — —\n"
        f"@UzbJobBot orqali e'lon bering ✅"
    )

    # 📢 Kanalga yuborиш
    if CHANNEL_ID:
        try:
            await bot.send_message(CHANNEL_ID, post)
            await m.answer("🫡 Ma'lumot @UzJobElonlar kanaliga joylandi ✅", reply_markup=kb_main())
        except Exception as e:
            await m.answer(f"⚠️ E'lon kanalga chiqolmadi: {e}", reply_markup=kb_main())

    # ✅ Базада сақлаш
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO seekers (tg_id, full_name, category, region, district, experience, salary, contact, extra) VALUES (?,?,?,?,?,?,?,?,?)",
            (m.from_user.id, full_name, category, region, district, experience, salary, contact, extra)
        )
        await db.commit()

    await state.clear()

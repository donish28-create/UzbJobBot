import asyncio
import aiosqlite
import os
import re
from typing import List, Dict

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from dotenv import load_dotenv

# -------------------- Env --------------------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0") or 0)
CHANNEL_ID = os.getenv("CHANNEL_ID")  # masalan: "@uzjobelonlar" yoki "-1001234567890"

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

REGIONS = {
    "Toshkent shahri": ["Chilonzor", "Yunusobod", "Mirzo Ulug‘bek", "Yakkasaroy", "Sergeli", "Bektemir"],
    "Andijon": ["Andijon shahar", "Asaka", "Baliqchi", "Paxtaobod", "Jalaquduq"],
    "Farg‘ona": ["Farg‘ona shahar", "Marg‘ilon", "Qo‘qon", "Oltiariq", "Rishton"],
    "Namangan": ["Namangan shahar", "Chortoq", "Uychi", "Pop", "To‘raqo‘rg‘on"],
    "Samarqand": ["Samarqand shahar", "Urgut", "Kattaqo‘rg‘on", "Ishtixon", "Nurobod"],
    "Buxoro": ["Buxoro shahar", "G‘ijduvon", "Kogon", "Vobkent", "Qorako‘l"],
    "Xorazm": ["Urganch", "Xiva", "Bog‘ot", "Yangiariq", "Shovot"],
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
    keys = [KeyboardButton(text=k) for k in REGIONS.keys()]
    keyboard = [keys[i:i+2] for i in range(0, len(keys), 2)]
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_districts(region):
    lst = REGIONS.get(region, [])
    if not lst:
        return ReplyKeyboardRemove()
    k = rows(lst, 2)
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
    extra = State()

# -------------------- Декоратор: Каналга аъзо текшириш --------------------
async def is_member(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# -------------------- Handlers --------------------
@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Assalomu alaykum! Bu <b>UzbJobBot</b>.\nSizga qanday yordam bera olaman?", reply_markup=kb_main())

# --- Seeker flow
@router.message(F.text == "👤 Ish kerak")
async def seeker_begin(m: Message, state: FSMContext):
    if not await is_member(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga aʼzo bo‘lish", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")]
        ])
        await m.answer("⚠️ Iltimos, avval kanalimizga aʼzo bo‘ling!", reply_markup=kb)
        return
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
    await m.answer("Yo‘nalishni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.custom_category, F.text)
async def seeker_custom_save(m: Message, state: FSMContext):
    await state.update_data(category=m.text.strip())
    await state.set_state(Seeker.region)
    await m.answer("Hududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.category)
async def seeker_category(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Seeker.region)
    await m.answer("Hududingizni tanlang:", reply_markup=kb_regions())

@router.message(Seeker.region)
async def seeker_region(m: Message, state: FSMContext):
    if m.text not in REGIONS:
        await m.answer("Iltimos, ro‘yxatdan hudud tanlang.")
        return
    await state.update_data(region=m.text)
    await state.set_state(Seeker.district)
    await m.answer("Tumaningizni tanlang:", reply_markup=kb_districts(m.text))

@router.message(Seeker.district)
async def seeker_district(m: Message, state: FSMContext):
    await state.update_data(district=m.text)
    await state.set_state(Seeker.experience)
    await m.answer("Tajribangiz (yil):", reply_markup=ReplyKeyboardRemove())

@router.message(Seeker.experience)
async def seeker_exp(m: Message, state: FSMContext):
    await state.update_data(experience=m.text.strip())
    await state.set_state(Seeker.salary)
    await m.answer("Qancha oylik kutyapsiz?")

@router.message(Seeker.salary)
async def seeker_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text.strip())
    await state.set_state(Seeker.contact)
    await m.answer("📞 Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Seeker.contact)
async def seeker_contact(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else m.text.strip()
    await state.update_data(contact=phone)
    await state.set_state(Seeker.extra)
    await m.answer("Qo‘shimcha maʼlumot (300 belgigacha):")

@router.message(Seeker.extra)
async def seeker_extra(m: Message, state: FSMContext):
    if len(m.text) > 300:
        await m.answer("❗ 300 belgidan oshmasin, qayta kiriting.")
        return
    data = await state.update_data(extra=m.text)
    data = await state.get_data()

    post = (
        f"🆕 <b>Ish qidiruvchi</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"🛠 {data['category']}\n"
        f"📍 {data['region']}, {data['district']}\n"
        f"🧰 Tajriba: {data['experience']}\n"
        f"💸 Maosh: {data['salary']}\n"
        f"📞 Aloqa: {data['contact']}\n"
        f"📝 {data['extra']}\n\n"
        f"📣 @UzbJobBot орқали эълон беринг"
    )

    if CHANNEL_ID:
        await bot.send_message(CHANNEL_ID, post)
    await m.answer("🫡 Ma’lumot @UzJobElonlar каналга жойланди ✅", reply_markup=kb_main())
    await state.clear()

# -------------------- Run --------------------
async def main():
    dp.include_router(router)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("CREATE TABLE IF NOT EXISTS seekers (id INTEGER PRIMARY KEY)")
        await db.commit()
    print("✅ Bot started.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

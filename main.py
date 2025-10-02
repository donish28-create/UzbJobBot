
import asyncio
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

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "REPLACE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
CHANNEL_ID = os.getenv("CHANNEL_ID")

if BOT_TOKEN in ("", "REPLACE", None):
    raise SystemExit("Please set BOT_TOKEN in environment or .env")

bot = Bot(BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher()
DB_PATH = "data.db"

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

INIT_SQL = """
CREATE TABLE IF NOT EXISTS seekers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER,
    full_name TEXT,
    category TEXT,
    region TEXT,
    experience TEXT,
    salary TEXT,
    contact TEXT,
    contact_visible INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS offers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tg_id INTEGER,
    full_name TEXT,
    category TEXT,
    region TEXT,
    headcount TEXT,
    salary TEXT,
    contact TEXT,
    contact_visible INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS counters (
    category TEXT PRIMARY KEY,
    seekers_count INTEGER DEFAULT 0,
    offers_count INTEGER DEFAULT 0
);
"""

async def db_init():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(INIT_SQL)
        for c in CATEGORIES:
            await db.execute("INSERT OR IGNORE INTO counters (category, seekers_count, offers_count) VALUES (?,0,0)", (c,))
        await db.commit()

def normalize_category(text: str) -> str:
    t = text.strip().lower()
    for c in CATEGORIES:
        if t == c.lower(): return c
    for canon, syns in CATEGORY_SYNONYMS.items():
        for s in syns:
            if s in t: return canon
    best = CATEGORIES[0]; best_score=-1
    for c in CATEGORIES:
        sc = len(set(t.split()) & set(c.lower().split()))
        if sc>best_score: best=c; best_score=sc
    return best

async def inc_counter(category: str, seeker: bool):
    async with aiosqlite.connect(DB_PATH) as db:
        if seeker:
            await db.execute("UPDATE counters SET seekers_count=seekers_count+1 WHERE category=?", (category,))
        else:
            await db.execute("UPDATE counters SET offers_count=offers_count+1 WHERE category=?", (category,))
        await db.commit()

async def get_counts(category: str):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT seekers_count, offers_count FROM counters WHERE category=?", (category,)) as cur:
            row = await cur.fetchone()
            return row if row else (0,0)

router = Router()

@router.message(CommandStart())
async def on_start(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Assalomu alaykum! Bu <b>UzbJobBot</b>.\nSizga qanday yordam bera olaman?", reply_markup=kb_main())

@router.message(F.text == "⬅️ Orqaga")
async def back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Asosiy menyu:", reply_markup=kb_main())

# Seeker flow
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
    guessed = normalize_category(m.text)
    await state.update_data(category=guessed)
    await state.set_state(Seeker.region)
    await m.answer(f"Yo‘nalish: <b>{guessed}</b>\nHududingizni tanlang:", reply_markup=kb_regions())

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

@router.message(Seeker.contact, F.contact)
async def seeker_contact_share(m: Message, state: FSMContext):
    await state.update_data(contact=m.contact.phone_number)
    await state.set_state(Seeker.contact_visible)
    await m.answer("Raqamingiz kanalda ko‘rinsinmi?", reply_markup=kb_visibility())

@router.message(Seeker.contact, F.text)
async def seeker_contact_text(m: Message, state: FSMContext):
    await state.update_data(contact=m.text.strip())
    await state.set_state(Seeker.contact_visible)
    await m.answer("Raqamingiz kanalda ko‘rinsinmi?", reply_markup=kb_visibility())

@router.message(Seeker.contact_visible, F.text.in_(["✅ Raqam ko‘rinsin","❌ Raqam ko‘rinmasin"]))
async def seeker_finish(m: Message, state: FSMContext):
    data = await state.get_data()
    contact_visible = 1 if m.text == "✅ Raqam ko‘rinsin" else 0
    full_name=data["full_name"]; category=data["category"]; region=data["region"]
    experience=data["experience"]; salary=data["salary"]; contact=data["contact"]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO seekers (tg_id, full_name, category, region, experience, salary, contact, contact_visible)
                            VALUES (?,?,?,?,?,?,?,?)""",
                         (m.from_user.id, full_name, category, region, experience, salary, contact, contact_visible))
        await db.commit()

    await inc_counter(category, seeker=True)
    s_count, o_count = await get_counts(category)

    phone_line = f"📞 Aloqa: {contact}" if contact_visible else "📩 Aloqa yashirin — botga yozing: @UzbJobBot"
    post = (f"🆕 <b>Ish qidiruvchi</b>\n\n"
            f"👤 {full_name}\n"
            f"🛠 Yo‘nalish: <b>{category}</b>\n"
            f"📍 Hudud: {region}\n"
            f"🧰 Tajriba: {experience}\n"
            f"💸 Maosh kutyapti: {salary}\n"
            f"{phone_line}\n— — —\n"
            f"#ish_kerak #{re.sub(r'[^a-zA-Z0-9]+','_', category.lower())}")
    if CHANNEL_ID:
        try: await bot.send_message(CHANNEL_ID, post)
        except Exception as e: await m.answer(f"⚠️ E'lon kanalda chiqolmadi: {e}")

    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, f"✅ Yangi ish qidiruvchi: {category}\n👥 Holat — ishchi: {s_count} | taklif: {o_count}")
        except Exception: pass

    await m.answer("Rahmat! Ma'lumot saqlandi ✅", reply_markup=kb_main())
    await state.clear()

# Employer flow
@router.message(F.text == "🏭 Ishchi kerak")
async def emp_begin(m: Message, state: FSMContext):
    await state.set_state(Employer.full_name)
    await m.answer("Ism familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.full_name, F.text)
async def emp_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text.strip())
    await state.set_state(Employer.category)
    await m.answer("Qaysi yo‘nalishda ishchi kerak?", reply_markup=kb_categories())

@router.message(Employer.category, F.text == "➕ Boshqa yo‘nalish")
async def emp_custom_prompt(m: Message, state: FSMContext):
    await state.set_state(Employer.custom_category)
    await m.answer("Yo‘nalishni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.custom_category, F.text)
async def emp_custom_save(m: Message, state: FSMContext):
    guessed = normalize_category(m.text)
    await state.update_data(category=guessed)
    await state.set_state(Employer.region)
    await m.answer(f"Yo‘nalish: <b>{guessed}</b>\nHududni tanlang:", reply_markup=kb_regions())

@router.message(Employer.category, F.text.in_([b for row in CATEGORY_BUTTON_ROWS for b in row]))
async def emp_category(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Employer.region)
    await m.answer("Hududni tanlang:", reply_markup=kb_regions())

@router.message(Employer.region, F.text.in_(REGIONS))
async def emp_region(m: Message, state: FSMContext):
    await state.update_data(region=m.text)
    await state.set_state(Employer.headcount)
    await m.answer("Nechta ishchi kerak? (son):", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.headcount, F.text)
async def emp_headcount(m: Message, state: FSMContext):
    await state.update_data(headcount=m.text.strip())
    await state.set_state(Employer.salary)
    await m.answer("Qancha oylik/taklif qilasiz? (so‘mda yoki $):")

@router.message(Employer.salary, F.text)
async def emp_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text.strip())
    await state.set_state(Employer.contact)
    await m.answer("Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Employer.contact, F.contact)
async def emp_contact_share(m: Message, state: FSMContext):
    await state.update_data(contact=m.contact.phone_number)
    await state.set_state(Employer.contact_visible)
    await m.answer("Raqamingiz kanalda ko‘rinsinmi?", reply_markup=kb_visibility())

@router.message(Employer.contact, F.text)
async def emp_contact_text(m: Message, state: FSMContext):
    await state.update_data(contact=m.text.strip())
    await state.set_state(Employer.contact_visible)
    await m.answer("Raqamingiz kanalda ko‘rinsinmi?", reply_markup=kb_visibility())

@router.message(Employer.contact_visible, F.text.in_(["✅ Raqam ko‘rinsin","❌ Raqam ko‘rinmasin"]))
async def emp_finish(m: Message, state: FSMContext):
    data = await state.get_data()
    contact_visible = 1 if m.text == "✅ Raqam ko‘rinsin" else 0
    full_name=data["full_name"]; category=data["category"]; region=data["region"]
    headcount=data["headcount"]; salary=data["salary"]; contact=data["contact"]

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""INSERT INTO offers (tg_id, full_name, category, region, headcount, salary, contact, contact_visible)
                            VALUES (?,?,?,?,?,?,?,?)""",
                         (m.from_user.id, full_name, category, region, headcount, salary, contact, contact_visible))
        await db.commit()

    await inc_counter(category, seeker=False)
    s_count, o_count = await get_counts(category)

    phone_line = f"📞 Aloqa: {contact}" if contact_visible else "📩 Aloqa yashirin — botga yozing: @UzbJobBot"
    post = (f"🆕 <b>Ish taklifi</b>\n\n"
            f"👤 {full_name}\n"
            f"🛠 Yo‘nalish: <b>{category}</b>\n"
            f"📍 Hudud: {region}\n"
            f"👥 Kerak: {headcount} nafar\n"
            f"💸 Oylik/taklif: {salary}\n"
            f"{phone_line}\n— — —\n"
            f"#ishchi_kerak #{re.sub(r'[^a-zA-Z0-9]+','_', category.lower())}")
    if CHANNEL_ID:
        try: await bot.send_message(CHANNEL_ID, post)
        except Exception as e: await m.answer(f"⚠️ E'lon kanalda chiqolmadi: {e}")

    if ADMIN_ID:
        try: await bot.send_message(ADMIN_ID, f"✅ Yangi ish taklifi: {category}\n👥 Holat — ishchi: {s_count} | taklif: {o_count}")
        except Exception: pass

    await m.answer("Rahmat! Ma'lumot saqlandi ✅", reply_markup=kb_main())
    await state.clear()

@dp.startup()
async def on_startup():
    await db_init()
    print("Bot started.")

def main():
    dp.include_router(router)
    asyncio.run(dp.start_polling(bot))

if __name__ == "__main__":
    main()

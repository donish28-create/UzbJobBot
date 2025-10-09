import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram import Router
import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()

# -------------------- HUDUDLAR --------------------
REGIONS = {
    "Toshkent shahri": ["Bektemir", "Chilonzor", "Mirzo Ulug‘bek", "Mirobod", "Olmazor", "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod", "Yunusobod"],
    "Toshkent viloyati": ["Bekobod", "Bo‘ka", "Chinoz", "Ohangaron", "Parkent", "Piskent", "Qibray", "Quyi Chirchiq", "O‘rta Chirchiq", "Yangiyo‘l", "Zangiota", "Toshkent tumani"],
    "Andijon": ["Andijon shahar", "Asaka", "Baliqchi", "Buloqboshi", "Izboskan", "Jalaquduq", "Marhamat", "Oltinko‘l", "Paxtaobod", "Shahrixon", "Ulug‘nor", "Xo‘jaobod"],
    "Farg‘ona": ["Farg‘ona shahar", "Oltiariq", "Bag‘dod", "Beshariq", "Dang‘ara", "Furqat", "Quva", "Qo‘qon", "Rishton", "So‘x", "Toshloq", "Uchko‘prik", "Yozyovon"],
    "Namangan": ["Namangan shahar", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq", "Norin", "Pop", "To‘raqo‘rg‘on", "Uchqo‘rg‘on", "Yangiqo‘rg‘on"],
    "Samarqand": ["Samarqand shahar", "Bulung‘ur", "Ishtixon", "Jomboy", "Kattaqo‘rg‘on", "Narpay", "Nurobod", "Oqdaryo", "Paxtachi", "Pastdarg‘om", "Payariq", "Qo‘shrabot", "Toyloq", "Urgut"],
}

# -------------------- Kategoriyalar --------------------
CATEGORY_BUTTON_ROWS = [
    ["Qurilish", "Haydovchilik"],
    ["Sotuv", "Ta’lim"],
    ["Tibbiyot", "Xizmat ko‘rsatish"],
]

# -------------------- Klaviatura funksiyalari --------------------
def rows(items, n=2):
    out, r = [], []
    for i, x in enumerate(items, 1):
        r.append(KeyboardButton(text=x))
        if i % n == 0:
            out.append(r)
            r = []
    if r:
        out.append(r)
    return out

def kb_main():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👤 Ish kerak")],
                  [KeyboardButton(text="🏭 Ishchi kerak")]],
        resize_keyboard=True
    )

def kb_categories():
    keyboard = []
    for a, b in CATEGORY_BUTTON_ROWS:
        keyboard.append([KeyboardButton(text=a), KeyboardButton(text=b)])
    keyboard.append([KeyboardButton(text="➕ Boshqa yo‘nalish")])
    keyboard.append([KeyboardButton(text="⬅️ Orqaga")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)

def kb_regions():
    keys = [KeyboardButton(text=k) for k in REGIONS.keys()]
    keyboard = [keys[i:i + 2] for i in range(0, len(keys), 2)]
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

# -------------------- FSM holatlar --------------------
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

class Employer(StatesGroup):
    full_name = State()
    category = State()
    custom_category = State()
    region = State()
    district = State()
    headcount = State()
    salary = State()
    contact = State()
    extra = State()

# -------------------- Foydalanuvchi kanal aʼzosi ekanligini tekshirish --------------------
async def is_member(user_id: int):
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# -------------------- /start --------------------
@router.message(CommandStart())
async def cmd_start(m: Message):
    await m.answer("Assalomu alaykum!\nQuyidagilardan birini tanlang 👇", reply_markup=kb_main())

# -------------------- Ish kerak flow --------------------
@router.message(F.text == "👤 Ish kerak")
async def ish_kerak(m: Message, state: FSMContext):
    if not await is_member(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga aʼzo bo‘lish", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")]
        ])
        await m.answer("⚠️ Iltimos, avval kanalimizga aʼzo bo‘ling!", reply_markup=kb)
        return
    await state.set_state(Seeker.full_name)
    await m.answer("Ism familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())

# -------------------- Ish beruvchi flow --------------------
@router.message(F.text == "🏭 Ishchi kerak")
async def emp_begin(m: Message, state: FSMContext):
    if not await is_member(m.from_user.id):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Kanalga aʼzo bo‘lish", url=f"https://t.me/{CHANNEL_ID.replace('@','')}")]
        ])
        await m.answer("⚠️ Iltimos, avval kanalimizga aʼzo bo‘ling!", reply_markup=kb)
        return
    await state.set_state(Employer.full_name)
    await m.answer("Ism familiyangizni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.full_name)
async def emp_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text.strip())
    await state.set_state(Employer.category)
    await m.answer("Qaysi yo‘nalishda ishchi kerak?", reply_markup=kb_categories())

@router.message(Employer.category, F.text == "➕ Boshqa yo‘nalish")
async def emp_custom_prompt(m: Message, state: FSMContext):
    await state.set_state(Employer.custom_category)
    await m.answer("Yo‘nalishni yozing:", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.custom_category)
async def emp_custom_save(m: Message, state: FSMContext):
    await state.update_data(category=m.text.strip())
    await state.set_state(Employer.region)
    await m.answer("Hududni tanlang:", reply_markup=kb_regions())

@router.message(Employer.category)
async def emp_category(m: Message, state: FSMContext):
    await state.update_data(category=m.text)
    await state.set_state(Employer.region)
    await m.answer("Hududni tanlang:", reply_markup=kb_regions())

@router.message(Employer.region)
async def emp_region(m: Message, state: FSMContext):
    if m.text not in REGIONS:
        await m.answer("Iltimos, ro‘yxatdan hudud tanlang.")
        return
    await state.update_data(region=m.text)
    await state.set_state(Employer.district)
    await m.answer("Tumaningizni tanlang:", reply_markup=kb_districts(m.text))

@router.message(Employer.district)
async def emp_district(m: Message, state: FSMContext):
    await state.update_data(district=m.text)
    await state.set_state(Employer.headcount)
    await m.answer("Nechta ishchi kerak?", reply_markup=ReplyKeyboardRemove())

@router.message(Employer.headcount)
async def emp_headcount(m: Message, state: FSMContext):
    await state.update_data(headcount=m.text.strip())
    await state.set_state(Employer.salary)
    await m.answer("Qancha oylik/taklif qilasiz?")

@router.message(Employer.salary)
async def emp_salary(m: Message, state: FSMContext):
    await state.update_data(salary=m.text.strip())
    await state.set_state(Employer.contact)
    await m.answer("📞 Aloqa raqamingizni yuboring:", reply_markup=kb_contact())

@router.message(Employer.contact)
async def emp_contact(m: Message, state: FSMContext):
    phone = m.contact.phone_number if m.contact else m.text.strip()
    await state.update_data(contact=phone)
    await state.set_state(Employer.extra)
    await m.answer("Qo‘shimcha maʼlumot (300 belgigacha):")

@router.message(Employer.extra)
async def emp_extra(m: Message, state: FSMContext):
    if len(m.text) > 300:
        await m.answer("❗ 300 belgidan oshmasin, qayta kiriting.")
        return
    data = await state.update_data(extra=m.text)
    data = await state.get_data()

    post = (
        f"🆕 <b>Ish taklifi</b>\n\n"
        f"👤 {data['full_name']}\n"
        f"🛠 {data['category']}\n"
        f"📍 {data['region']}, {data['district']}\n"
        f"👥 Kerak: {data['headcount']} nafar\n"
        f"💸 Oylik: {data['salary']}\n"
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
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

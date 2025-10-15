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
from matching import setup_matching
from database import db_init
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()
router = Router()

# -------------------- HUDUDLAR --------------------
REGIONS = {
    "Butun Oʻzbekiston boʻyicha": [],

    "Toshkent shahri": [
        "Bektemir tumani", "Chilonzor tumani", "Yashnobod tumani", "Mirobod tumani",
        "Mirzo Ulugʻbek tumani", "Sergeli tumani", "Shayxontohur tumani", "Olmazor tumani",
        "Uchtepa tumani", "Yakkasaroy tumani", "Yunusobod tumani"
    ],

    "Toshkent viloyati": [
        "Bekobod tumani", "Boʻstonliq tumani", "Boʻka tumani", "Chinoz tumani", "Qibray tumani",
        "Ohangaron tumani", "Oqqoʻrgʻon tumani", "Parkent tumani", "Piskent tumani",
        "Quyi Chirchiq tumani", "Oʻrta Chirchiq tumani", "Yangiyoʻl tumani",
        "Yuqori Chirchiq tumani", "Zangiota tumani"
    ],

    "Andijon": [
        "Andijon tumani", "Asaka tumani", "Baliqchi tumani", "Boʻston tumani", "Buloqboshi tumani",
        "Izboskan tumani", "Jalaquduq tumani", "Xoʻjaobod tumani", "Qoʻrgʻontepa tumani",
        "Marhamat tumani", "Oltinkoʻl tumani", "Paxtaobod tumani", "Shahrixon tumani",
        "Ulugʻnor tumani"
    ],

    "Fargʻona": [
        "Oltiariq tumani", "Bagʻdod tumani", "Beshariq tumani", "Buvayda tumani", "Dangʻara tumani",
        "Fargʻona tumani", "Furqat tumani", "Qoʻshtepa tumani", "Quva tumani", "Rishton tumani",
        "Soʻx tumani", "Toshloq tumani", "Uchkoʻprik tumani", "Oʻzbekiston tumani", "Yozyovon tumani"
    ],

    "Namangan": [
        "Chortoq tumani", "Chust tumani", "Kosonsoy tumani", "Mingbuloq tumani",
        "Namangan tumani", "Norin tumani", "Pop tumani", "Toʻraqoʻrgʻon tumani",
        "Uchqoʻrgʻon tumani", "Uychi tumani", "Yangiqoʻrgʻon tumani"
    ],

    "Samarqand": [
        "Bulungʻur tumani", "Ishtixon tumani", "Jomboy tumani", "Kattaqoʻrgʻon tumani",
        "Qoʻshrabot tumani", "Narpay tumani", "Nurobod tumani", "Oqdaryo tumani",
        "Paxtachi tumani", "Payariq tumani", "Pastdargʻom tumani", "Samarqand tumani",
        "Toyloq tumani", "Urgut tumani"
    ],

    "Buxoro": [
        "Olot tumani", "Buxoro tumani", "Gʻijduvon tumani", "Jondor tumani", "Kogon tumani",
        "Qorakoʻl tumani", "Qorovulbozor tumani", "Peshku tumani", "Romitan tumani",
        "Shofirkon tumani", "Vobkent tumani"
    ],

    "Navoiy": [
        "Konimex tumani", "Karmana tumani", "Qiziltepa tumani", "Xatirchi tumani",
        "Navbahor tumani", "Nurota tumani", "Tomdi tumani", "Uchquduq tumani"
    ],

    "Xorazm": [
        "Bogʻot tumani", "Gurlan tumani", "Xonqa tumani", "Hazorasp tumani", "Xiva tumani",
        "Qoʻshkoʻpir tumani", "Shovot tumani", "Urganch tumani", "Yangiariq tumani",
        "Yangibozor tumani", "Tuproqqalʼa tumani"
    ],

    "Qashqadaryo": [
        "Chiroqchi tumani", "Dehqonobod tumani", "Gʻuzor tumani", "Qamashi tumani",
        "Qarshi tumani", "Koson tumani", "Kasbi tumani", "Kitob tumani", "Mirishkor tumani",
        "Muborak tumani", "Nishon tumani", "Shahrisabz tumani", "Yakkabogʻ tumani",
        "Koʻkdala tumani"
    ],

    "Surxondaryo": [
        "Angor tumani", "Boysun tumani", "Denov tumani", "Jarqoʻrgʻon tumani", "Qiziriq tumani",
        "Qumqoʻrgʻon tumani", "Muzrabot tumani", "Oltinsoy tumani", "Sariosiyo tumani",
        "Sherobod tumani", "Shoʻrchi tumani", "Termiz tumani", "Uzun tumani", "Bandixon tumani"
    ],

    "Jizzax": [
        "Arnasoy tumani", "Baxmal tumani", "Doʻstlik tumani", "Forish tumani", "Gʻallaorol tumani",
        "Sharof Rashidov tumani", "Mirzachoʻl tumani", "Paxtakor tumani", "Yangiobod tumani",
        "Zomin tumani", "Zafarobod tumani", "Zarbdor tumani"
    ],

    "Sirdaryo": [
        "Oqoltin tumani", "Boyovut tumani", "Guliston tumani", "Xovos tumani", "Mirzaobod tumani",
        "Sayxunobod tumani", "Sardoba tumani", "Sirdaryo tumani"
    ],

    "Qoraqalpogʻiston R.": [
        "Amudaryo tumani", "Beruniy tumani", "Chimboy tumani", "Ellikqalʼa tumani", "Kegeyli tumani",
        "Moʻynoq tumani", "Nukus tumani", "Qanlikoʻl tumani", "Qoʻngʻirot tumani", "Qoraoʻzak tumani",
        "Shumanay tumani", "Taxtakoʻpir tumani", "Toʻrtkoʻl tumani", "Xoʻjayli tumani",
        "Taxiatosh tumani", "Boʻzatov tumani"
    ]
}

# -------------------- Kategoriyalar --------------------
CATEGORY_BUTTON_ROWS = [
    ["Qurilish", "Haydovchilik"],
    ["Sotuv / Savdo", "Ta’lim / O‘qituvchilik"],
    ["Tibbiyot / Farmatsevtika", "Xizmat ko‘rsatish"],
    ["IT / Dasturlash", "Marketing / Raqamli marketing"],
    ["Ofis / Buxgalteriya", "Bank / Moliya"],
    ["Restoran / Oshxona", "Go‘zallik / Sartaroshxona"],
    ["Xavfsizlik / Qo‘riqlash", "Logistika / Omborxona"],
    ["Fermerlik / Qishloq xo‘jaligi", "Ishlab chiqarish / Zavod"],
    ["Telekommunikatsiya", "Dizayn / Grafika"],
    ["Advokat / Yurist", "Tarjima / Kontent yaratuvchi"],
    ["Tikuvchilik / Moda", "Avtoservis / Usta"],
    ["Elektromontyor / Texnik", "SMM / Reklama"],
    ["Freelance / Masofaviy ish", "Kurier / Yetkazib berish"],
    ["Ko‘ngilochar soha", "Sport / Fitness"],
    ["Davlat xizmati / Ma’muriyat", "HR / Kadrlar bo‘limi"],
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

# -------------------- Orqaga қайтиш (ҳар хил ҳолатлар) --------------------
@router.message(Seeker.category, F.text == "⬅️ Orqaga")
@router.message(Seeker.region, F.text == "⬅️ Orqaga")
@router.message(Seeker.district, F.text == "⬅️ Orqaga")
async def seeker_back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Bosh sahifaga qaytdingiz 👇", reply_markup=kb_main())

@router.message(Seeker.full_name)
async def seeker_name(m: Message, state: FSMContext):
    await state.update_data(full_name=m.text.strip())
    await state.set_state(Seeker.category)
    await m.answer("Qaysi yo‘nalishda ish qidiryapsiz?", reply_markup=kb_categories())


@router.message(Seeker.category, F.text == "➕ Boshqa yo‘nalish")
async def seeker_custom_prompt(m: Message, state: FSMContext):
    await state.set_state(Seeker.custom_category)
    await m.answer("Yo‘nalishni yozing:", reply_markup=ReplyKeyboardRemove())


@router.message(Seeker.custom_category)
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
async def seeker_experience(m: Message, state: FSMContext):
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
        f"💸 Maosh kutyapti: {data['salary']}\n"
        f"📞 Aloqa: {data['contact']}\n"
        f"📝 {data['extra']}\n\n"
        f"📣 @UzbJobBot орқали эълон беринг"
    )

    if CHANNEL_ID:
        await bot.send_message(CHANNEL_ID, post)
    await m.answer("🫡 Ma’lumot @UzJobElonlar каналга жойланди ✅", reply_markup=kb_main())
    await state.clear()

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

# -------------------- Orqaga қайтиш (иш берувчи учун) --------------------
@router.message(Employer.category, F.text == "⬅️ Orqaga")
@router.message(Employer.region, F.text == "⬅️ Orqaga")
@router.message(Employer.district, F.text == "⬅️ Orqaga")
async def employer_back(m: Message, state: FSMContext):
    await state.clear()
    await m.answer("Bosh sahifaga qaytdingiz 👇", reply_markup=kb_main())

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
    await db_init()  # база яратилади ёки текширилади
    dp.include_router(router)
    setup_matching(dp, bot)
    print("✅ Bot started (worker mode).")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

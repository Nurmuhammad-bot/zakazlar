"""
Telegram Buyurtma Bot (aiogram 3.x + Claude AI)
- 3 marta bekor = 15 daqiqa blok
- Telefon raqami guruhda yashirin ko'rinadi
pip install aiogram python-dotenv anthropic
"""
 
import asyncio
import logging
import re
import anthropic
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
 
load_dotenv()
BOT_TOKEN     = os.getenv("BOT_TOKEN")
GROUP_ID      = int(os.getenv("GROUP_ID"))
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
 
logging.basicConfig(level=logging.INFO)
bot    = Bot(token=BOT_TOKEN)
dp     = Dispatcher(storage=MemoryStorage())
client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
 
# Blok tizimi: {user_id: {"count": 0, "blocked_until": None}}
bekor_hisobi = {}
 
BLOCK_MINUTES = 15
MAX_BEKOR     = 3
 
 
def secret_phone(phone: str) -> str:
    """Telefon raqamini yashiradi: +998901234567 → +998 9** ***567"""
    if len(phone) >= 10:
        return phone[:5] + " " + phone[5] + "** ***" + phone[-3:]
    return "***"
 
 
def is_blocked(user_id: int) -> tuple[bool, int]:
    """Foydalanuvchi bloklanganmi? (blokmi, qolgan daqiqa)"""
    if user_id not in bekor_hisobi:
        return False, 0
    data = bekor_hisobi[user_id]
    if data.get("blocked_until") and datetime.now() < data["blocked_until"]:
        qoldi = int((data["blocked_until"] - datetime.now()).total_seconds() / 60) + 1
        return True, qoldi
    return False, 0
 
 
def add_bekor(user_id: int) -> int:
    """Bekor sonini oshiradi, kerak bo'lsa bloklaydi. Qaytaradi: qolgan urinish"""
    if user_id not in bekor_hisobi:
        bekor_hisobi[user_id] = {"count": 0, "blocked_until": None}
 
    # Blok vaqti o'tgan bo'lsa reset
    data = bekor_hisobi[user_id]
    if data.get("blocked_until") and datetime.now() >= data["blocked_until"]:
        data["count"] = 0
        data["blocked_until"] = None
 
    data["count"] += 1
 
    if data["count"] >= MAX_BEKOR:
        data["blocked_until"] = datetime.now() + timedelta(minutes=BLOCK_MINUTES)
        data["count"] = 0
        return 0  # bloklandi
 
    return MAX_BEKOR - data["count"]  # qolgan urinish
 
 
def find_best_site(mahsulot: str, miqdor: str) -> str:
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": (
                f"Mahsulot: {mahsulot}, miqdor: {miqdor}\n\n"
                "O'zbekistonda bu mahsulotni qaysi saytda eng arzon va tez topish mumkin?\n"
                "Uzum.uz, Olx.uz, Wildberries.uz, Ozon.uz taqqoslab:\n"
                "- Eng yaxshi sayt\n"
                "- Taxminiy narx (so'mda)\n"
                "- Sayt linki\n"
                "Qisqa va aniq javob ber."
            )
        }]
    )
    return response.content[0].text
 
 
class Zakaz(StatesGroup):
    ism        = State()
    nomer      = State()
    manzil     = State()
    mahsulot   = State()
    miqdor     = State()
    tasdiqlash = State()
 
 
@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    blocked, qoldi = is_blocked(user_id)
    if blocked:
        await message.answer(f"🚫 Siz {qoldi} daqiqaga bloklandingiz.\nKeyinroq urinib ko'ring.")
        return
    await state.clear()
    await message.answer(
        "👋 Salom! Smart Buyurtma Botiga xush kelibsiz!\n\n"
        "🤖 Mahsulotingizni ayting — men eng arzon saytni o'zim topaman!\n\n"
        "Boshlash uchun /zakaz bosing.",
        reply_markup=ReplyKeyboardRemove()
    )
 
 
@dp.message(Command("zakaz"))
async def zakaz_handler(message: Message, state: FSMContext):
    user_id = message.from_user.id
    blocked, qoldi = is_blocked(user_id)
    if blocked:
        await message.answer(f"🚫 Siz {qoldi} daqiqaga bloklandingiz.\nKeyinroq urinib ko'ring.")
        return
    await state.set_state(Zakaz.ism)
    await message.answer(
        "📋 Buyurtma boshlandi!\n\n"
        "1️⃣  Ism va familiyangizni yozing:",
        reply_markup=ReplyKeyboardRemove()
    )
 
 
@dp.message(Zakaz.ism)
async def get_ism(message: Message, state: FSMContext):
    await state.update_data(ism=message.text)
    await state.set_state(Zakaz.nomer)
    await message.answer("2️⃣  Telefon raqamingizni yozing 📱\n(Masalan: +998901234567)")
 
 
@dp.message(Zakaz.nomer)
async def get_nomer(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not re.match(r'^\+998\d{9}$', phone):
        await message.answer("❌ Noto'g'ri format!\nMasalan: +998901234567")
        return
    await state.update_data(nomer=phone)
    await state.set_state(Zakaz.manzil)
    await message.answer("3️⃣  Yetkazib berish manzilini yozing 📍")
 
 
@dp.message(Zakaz.manzil)
async def get_manzil(message: Message, state: FSMContext):
    await state.update_data(manzil=message.text)
    await state.set_state(Zakaz.mahsulot)
    await message.answer("4️⃣  Qaysi mahsulotni xohlaysiz? 🛒")
 
 
@dp.message(Zakaz.mahsulot)
async def get_mahsulot(message: Message, state: FSMContext):
    await state.update_data(mahsulot=message.text)
    await state.set_state(Zakaz.miqdor)
    await message.answer("5️⃣  Miqdorini yozing 🔢\n(Masalan: 2 dona)")
 
 
@dp.message(Zakaz.miqdor)
async def get_miqdor(message: Message, state: FSMContext):
    await state.update_data(miqdor=message.text)
    d = await state.get_data()
 
    await message.answer("🤖 AI eng arzon saytni qidiryapti... ⏳")
 
    try:
        sayt_tavsiya = find_best_site(d['mahsulot'], d['miqdor'])
    except Exception:
        sayt_tavsiya = "Uzum.uz yoki Olx.uz da qidiring"
 
    await state.update_data(sayt=sayt_tavsiya)
 
    xulosa = (
        "✅ Buyurtma ma'lumotlari:\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Ism:      {d['ism']}\n"
        f"📞 Telefon:  {secret_phone(d['nomer'])}\n"
        f"📍 Manzil:   {d['manzil']}\n"
        f"🛒 Mahsulot: {d['mahsulot']}\n"
        f"🔢 Miqdor:   {d['miqdor']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 AI tavsiyasi:\n{sayt_tavsiya}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Tasdiqlaysizmi?"
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Ha, tasdiqlash")],
            [KeyboardButton(text="❌ Yo'q, bekor qilish")]
        ],
        resize_keyboard=True
    )
    await state.set_state(Zakaz.tasdiqlash)
    await message.answer(xulosa, reply_markup=keyboard)
 
 
@dp.message(Zakaz.tasdiqlash, F.text == "✅ Ha, tasdiqlash")
async def confirm_yes(message: Message, state: FSMContext):
    d = await state.get_data()
    user = message.from_user
 
    # Tasdiqlashda bekor hisobini reset qilish
    if user.id in bekor_hisobi:
        bekor_hisobi[user.id]["count"] = 0
 
    await message.answer(
        "🎉 Buyurtmangiz qabul qilindi!\n"
        "Tez orada siz bilan bog'lanamiz. Rahmat!",
        reply_markup=ReplyKeyboardRemove()
    )
 
    guruh_xabar = (
        "🛒 YANGI ZAKAZ!\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Ism:      {d['ism']}\n"
        f"📞 Telefon:  {d['nomer']}\n"
        f"📍 Manzil:   {d['manzil']}\n"
        f"🛍 Mahsulot: {d['mahsulot']}\n"
        f"🔢 Miqdor:   {d['miqdor']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 AI tavsiyasi:\n{d['sayt']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 @{user.username or 'username yoq'}\n"
        f"✅ {d['ism']} zakaz qildi!"
    )
    await bot.send_message(chat_id=GROUP_ID, text=guruh_xabar)
    await state.clear()
 
 
@dp.message(Zakaz.tasdiqlash, F.text == "❌ Yo'q, bekor qilish")
async def confirm_no(message: Message, state: FSMContext):
    user_id = message.from_user.id
    await state.clear()
 
    qoldi = add_bekor(user_id)
 
    if qoldi == 0:
        await message.answer(
            f"🚫 Siz {MAX_BEKOR} marta bekor qildingiz!\n"
            f"⏳ {BLOCK_MINUTES} daqiqaga bloklandingiz.",
            reply_markup=ReplyKeyboardRemove()
        )
    else:
        await message.answer(
            f"❌ Bekor qilindi.\n"
            f"⚠️ Diqqat: Yana {qoldi} marta bekor qilsangiz, bloklanasiz!\n\n"
            "Qaytadan boshlash uchun /zakaz yozing.",
            reply_markup=ReplyKeyboardRemove()
        )
 
 
@dp.message(Command("bekor"))
async def bekor_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
 
 
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())

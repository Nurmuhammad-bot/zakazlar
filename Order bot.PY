"""
Telegram Buyurtma Bot (aiogram 3.x + Claude AI)
Bot mahsulotni qabul qilib, Claude orqali eng arzon saytni topadi
pip install aiogram python-dotenv anthropic
"""
 
import asyncio
import logging
import re
import anthropic
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
 
 
class Zakaz(StatesGroup):
    ism        = State()
    nomer      = State()
    manzil     = State()
    mahsulot   = State()
    miqdor     = State()
    tasdiqlash = State()
 
 
def find_best_site(mahsulot: str, miqdor: str) -> str:
    """Claude API orqali eng arzon saytni topadi"""
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Mahsulot: {mahsulot}\n"
                    f"Miqdor: {miqdor}\n\n"
                    "O'zbekistonda bu mahsulotni sotadigan saytlarni tahlil qil. "
                    "Uzum.uz, Olx.uz, Wildberries.uz, Ozon.uz kabi saytlardan "
                    "qaysi birida eng arzon va qulay bo'lishini ayt.\n\n"
                    "Qisqa javob ber (3-5 qator):\n"
                    "1. Eng yaxshi sayt va taxminiy narx\n"
                    "2. Sababi (arzonligi, yetkazib berishi)\n"
                    "3. Sayt linki"
                )
            }
        ]
    )
    return response.content[0].text
 
 
@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Salom! Smart Buyurtma Botiga xush kelibsiz!\n\n"
        "🤖 Men mahsulotingizni qabul qilib,\n"
        "eng arzon saytni avtomatik topaman!\n\n"
        "Boshlash uchun /zakaz buyrug'ini bosing.",
        reply_markup=ReplyKeyboardRemove()
    )
 
 
@dp.message(Command("zakaz"))
async def zakaz_handler(message: Message, state: FSMContext):
    await state.set_state(Zakaz.ism)
    await message.answer(
        "📋 Buyurtma boshlandi!\n\n"
        "1️⃣  Ism va familiyangizni yozing:\n"
        "(Masalan: Alisher Karimov)",
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
    await message.answer("4️⃣  Qaysi mahsulotni xohlaysiz? 🛒\n(Masalan: Nike Air Max 90, iPhone 15, Samsung TV)")
 
 
@dp.message(Zakaz.mahsulot)
async def get_mahsulot(message: Message, state: FSMContext):
    await state.update_data(mahsulot=message.text)
    await state.set_state(Zakaz.miqdor)
    await message.answer("5️⃣  Miqdorini yozing 🔢\n(Masalan: 2 dona)")
 
 
@dp.message(Zakaz.miqdor)
async def get_miqdor(message: Message, state: FSMContext):
    await state.update_data(miqdor=message.text)
    d = await state.get_data()
 
    # AI tahlil qilmoqda
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
        f"📞 Telefon:  {d['nomer']}\n"
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
    await state.clear()
    await message.answer(
        "❌ Bekor qilindi. /zakaz orqali qaytadan boshlang.",
        reply_markup=ReplyKeyboardRemove()
    )
 
 
@dp.message(Command("bekor"))
async def bekor_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
 
 
@dp.message(Command("getid"))
async def getid_handler(message: Message):
    await message.answer(f"Bu chatning ID si: {message.chat.id}")
 
 
async def main():
    print("✅ Bot ishga tushdi...")
    await dp.start_polling(bot)
 
 
if __name__ == "__main__":
    asyncio.run(main())

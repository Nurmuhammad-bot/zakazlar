import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os
 
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID  = int(os.getenv("GROUP_ID"))
 
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
dp  = Dispatcher(storage=MemoryStorage())
 
 
class Zakaz(StatesGroup):
    ism        = State()
    nomer      = State()
    manzil     = State()
    mahsulot   = State()
    miqdor     = State()
    sayt       = State()
    tasdiqlash = State()
 
 
@dp.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Salom! Buyurtma botiga xush kelibsiz!\n\n"
        "Buyurtma berish uchun /zakaz buyrug'ini bosing.",
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
    await message.answer("4️⃣  Mahsulot nomi yoki linkini yozing 🛒")
 
 
@dp.message(Zakaz.mahsulot)
async def get_mahsulot(message: Message, state: FSMContext):
    await state.update_data(mahsulot=message.text)
    await state.set_state(Zakaz.miqdor)
    await message.answer("5️⃣  Miqdorini yozing 🔢 (Masalan: 2 dona)")
 
 
@dp.message(Zakaz.miqdor)
async def get_miqdor(message: Message, state: FSMContext):
    await state.update_data(miqdor=message.text)
    await state.set_state(Zakaz.sayt)
    await message.answer("6️⃣  Qaysi saytdan zakaz qilaylik? 🌐")
 
 
@dp.message(Zakaz.sayt)
async def get_sayt(message: Message, state: FSMContext):
    await state.update_data(sayt=message.text)
    d = await state.get_data()
    xulosa = (
        "✅ Buyurtma ma'lumotlari:\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Ism:       {d['ism']}\n"
        f"📞 Telefon:   {d['nomer']}\n"
        f"📍 Manzil:    {d['manzil']}\n"
        f"🛒 Mahsulot:  {d['mahsulot']}\n"
        f"🔢 Miqdor:    {d['miqdor']}\n"
        f"🌐 Sayt:      {d['sayt']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "Ma'lumotlar to'g'rimi?"
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
        f"👤 Ism:        {d['ism']}\n"
        f"📞 Telefon:    {d['nomer']}\n"
        f"📍 Manzil:     {d['manzil']}\n"
        f"🛍 Mahsulot:   {d['mahsulot']}\n"
        f"🔢 Miqdor:     {d['miqdor']}\n"
        f"🌐 Sayt:       {d['sayt']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 Telegram:   @{user.username or 'username yoq'}\n"
        f"\n✅ {d['ism']} zakaz qildi!"
    )
    await bot.send_message(chat_id=GROUP_ID, text=guruh_xabar)
    await state.clear()
 
 
@dp.message(Zakaz.tasdiqlash, F.text == "❌ Yo'q, bekor qilish")
async def confirm_no(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Buyurtma bekor qilindi.\n"
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
    asyncio.run(main())

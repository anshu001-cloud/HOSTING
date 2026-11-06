import os
import time
import threading
import asyncio
import subprocess
from flask import Flask
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==============================================================================
# CONFIGURATION (Yahan apna Token aur link daal)
# ==============================================================================
API_TOKEN = '8609021514:AAExZLAsVAAgEPFAuzZeoT-V3U3DWFiBfzU' 
MY_CHANNEL_LINK = 'https://t.me/anshuhtt' 
ADMIN_USERNAME = 'b_babu00' 
# ==============================================================================

# --- 1. DUMMY WEB SERVER (Render ko zinda rakhne ke liye) ---
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is alive and running 24/7!"

def run_web_server():
    # Render "PORT" environment variable deta hai
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# --- 2. TELEGRAM BOT SETUP ---
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📢 Join Channel", url=MY_CHANNEL_LINK))
    builder.row(
        InlineKeyboardButton(text="ℹ️ About", callback_data="about"),
        InlineKeyboardButton(text="👨‍💻 Admin", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        f"👋 Welcome {message.from_first_name if hasattr(message, 'from_first_name') else message.from_user.first_name}!\n\n"
        "Main ek Hosting Bot hoon. Mujhe apni <b>.py</b> file bhejo, "
        "main usko host kar dunga.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "about")
async def about_cb(call: types.CallbackQuery):
    await call.message.answer("Yeh ek private hosting bot hai. Render pe 24/7 online.")
    await call.answer()

@dp.message(F.document)
async def handle_file(message: types.Message):
    doc = message.document
    if not doc.file_name.endswith('.py'):
        await message.answer("❌ Sirf <b>.py</b> file allowed hai.", parse_mode="HTML")
        return

    msg = await message.answer("⏳ File receive ho rahi hai...")
    
    user_id = message.from_user.id
    file_path = f"./{user_id}_{doc.file_name}"
    
    try:
        await bot.download(doc, destination=file_path)
        await msg.edit_text("🚀 File run ho rahi hai (Without Docker)...")

        # Render ke andar Docker allow nahi hota, isliye direct subprocess se run kar rahe hain
        # NOTE: Render pe agar user koi galat script bhejega, toh pura server crash ho sakta hai. 
        process = subprocess.Popen(
            ["python", file_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(3) # Wait to see if it crashes instantly
        if process.poll() is not None:
            _, stderr = process.communicate()
            await msg.edit_text(f"❌ File crash ho gayi!\n\nError:\n<pre>{stderr.decode('utf-8')[:300]}</pre>", parse_mode="HTML")
        else:
            await msg.edit_text("✅ <b>Deployed Successfully!</b>\n\nTera bot Render pe chal raha hai.")

    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)


if __name__ == "__main__":
    # 1. Web server ko background mein chalao (Render requirement)
    print("Starting Web Server for Render...")
    threading.Thread(target=run_web_server, daemon=True).start()

    # 2. Telegram Bot ko main loop mein chalao
    print("Starting Telegram Bot...")
    asyncio.run(dp.start_polling(bot))
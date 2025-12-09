from telegram.ext import Application, MessageHandler, filters
import logging

logging.basicConfig(level=logging.INFO)

TOKEN = "8010889318:AAGhZ0wuA6IypS0tXhTUtDnWQZg5b-Ir6us"

def handle_message(update, context):
    msg = update.message
    print("\n" + "="*60)
    print(f"📌 المجموعة: {msg.chat.title}")
    print(f"🆔 Chat ID: {msg.chat.id}")
    print(f"🗂️ Thread ID: {msg.message_thread_id}")
    print(f"📨 Message ID: {msg.message_id}")
    print(f"👤 من: {msg.from_user.first_name if msg.from_user else 'غير معروف'}")
    print(f"📝 نص الرسالة: {msg.text if msg.text else 'لا يوجد نص'}")
    print("="*60 + "\n")

def main():
    print("🚀 تشغيل بوت الحصول على المعرفات...")
    print("📤 أرسل رسالة في المجموعة وسأعرض المعلومات")
    print("🛑 اضغط Ctrl+C لإيقاف البوت\n")
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
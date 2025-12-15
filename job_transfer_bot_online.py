import traceback
import asyncio
import logging
import os
import time
import glob

import requests, sys


from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# 🔇 إيقاف logs مكتبة httpx (مكتبة الطلبات HTTP)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 🔧 إنشاء مجلد logs إذا لم يكن موجوداً
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 🔧 إعدادات التسجيل المتقدمة
def setup_logging():
    # إنشاء الـ logger الرئيسي
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # تنسيق الرسائل
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 1. Handler للعرض على الشاشة (فقط رسائلنا، ليس httpx)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    
    # فلتر لإخفاء logs httpx من الشاشة
    class NoHttpxFilter(logging.Filter):
        def filter(self, record):
            # إخفاء رسائل httpx و HTTP و API
            return not (
                'httpx' in record.name.lower() or 
                'http' in record.name.lower() or
                'api.telegram.org' in str(record.msg)
            )
    
    console_handler.addFilter(NoHttpxFilter())
    
    # 2. Handler للتدوير حسب الحجم والتاريخ (يحفظ كل شيء)
    log_filename = f"{LOG_DIR}/job_bot_{datetime.now().strftime('%Y-%m-%d')}.log"
    
    file_handler = RotatingFileHandler(
        filename=log_filename,
        maxBytes=1024 * 1024,  # 1 ميجابايت كحد أقصى لكل ملف
        backupCount=10,        # يحفظ 10 ملفات قديمة
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    
    # إزالة أي handlers موجودة مسبقاً
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # إضافة الـ handlers الجديدة
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)

# 🔄 دالة لتنظيف الملفات القديمة (أكثر من 60 يوم)
def clean_old_logs(days_to_keep=60):
    """حذف ملفات الـ logs الأقدم من عدد محدد من الأيام"""
    try:
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)  # ثواني في اليوم
        deleted_files = 0
        total_size_saved = 0
        
        # البحث عن جميع ملفات الـ logs
        log_patterns = [
            f"{LOG_DIR}/job_bot_*.log",
            f"{LOG_DIR}/job_bot_*.log.*"
        ]
        
        for pattern in log_patterns:
            for log_file in glob.glob(pattern):
                try:
                    if os.path.getmtime(log_file) < cutoff_time:
                        file_size = os.path.getsize(log_file)
                        os.remove(log_file)
                        deleted_files += 1
                        total_size_saved += file_size
                        logger.info(f"🧹 تم حذف الملف القديم: {os.path.basename(log_file)} ({file_size/1024:.1f} KB)")
                except Exception as e:
                    logger.warning(f"⚠️ تعذر حذف الملف {log_file}: {e}")
        
        if deleted_files > 0:
            logger.info(f"✅ تم تنظيف {deleted_files} ملف قديم، تم توفير {total_size_saved/(1024*1024):.2f} MB")
        else:
            logger.info("✅ لا توجد ملفات قديمة للحذف")
            
    except Exception as e:
        logger.error(f"❌ خطأ في تنظيف الملفات القديمة: {e}")

# 🔍 دالة لعرض معلومات المساحة
def get_logs_info():
    """عرض معلومات عن حجم وتوزيع ملفات الـ logs"""
    try:
        total_size = 0
        file_count = 0
        oldest_file = None
        newest_file = None
        
        for log_file in glob.glob(f"{LOG_DIR}/job_bot_*.log*"):
            try:
                file_size = os.path.getsize(log_file)
                file_time = os.path.getmtime(log_file)
                total_size += file_size
                file_count += 1
                
                if oldest_file is None or file_time < oldest_file[1]:
                    oldest_file = (log_file, file_time)
                if newest_file is None or file_time > newest_file[1]:
                    newest_file = (log_file, file_time)
            except:
                continue
        
        info = {
            'total_files': file_count,
            'total_size_mb': total_size / (1024 * 1024),
            'oldest_date': datetime.fromtimestamp(oldest_file[1]).strftime('%Y-%m-%d') if oldest_file else 'لا يوجد',
            'newest_date': datetime.fromtimestamp(newest_file[1]).strftime('%Y-%m-%d') if newest_file else 'لا يوجد'
        }
        return info
    except Exception as e:
        logger.error(f"❌ خطأ في قراءة معلومات الملفات: {e}")
        return None

# تهيئة الـ logger
logger = setup_logging()

# 🔑 بياناتك الخاصة
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    # هذا يطبع تحذيراً في حالة تشغيل البوت محلياً دون تعريف المتغير
    print("تحذير: لم يتم تعيين متغير البيئة 'TELEGRAM_BOT_TOKEN'.")
    # يمكنك وضع توكن تجريبي هنا للاختبار المحلي فقط، ولكن احذفه عند الرفع.
    # TOKEN = "توكن_تجريبي_هنا"
GROUP_CHAT_ID = -1002362405787
SMSM_NEW_JOBS_TOPIC_ID = 2
Habhoubeh_NEW_JOBS_TOPIC_ID = 62
APPLIED_JOBS_TOPIC_ID = 3

# 🎯 أزرار البوت
APPLY_BUTTON = InlineKeyboardMarkup([
    [InlineKeyboardButton("✅ الانتهاء من التقديم", callback_data="move_to_applied")]
])

CONFIRM_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("نعم، انتهيت ✅", callback_data="confirm_move"),
        InlineKeyboardButton("لا، إلغاء ❌", callback_data="cancel_move")
    ]
])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دالة /start"""
    await update.message.reply_text("🚀 البوت جاهز للعمل!")
    logger.info("✅ أمر /start تم استقباله")

async def handle_new_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة جميع الرسائل في توبيك الوظائف"""
    
    message = update.message
    
    # التحقق من المجموعة والتوبيك الصحيح
    if (message.chat.id == GROUP_CHAT_ID and 
        (message.message_thread_id == SMSM_NEW_JOBS_TOPIC_ID or message.message_thread_id == Habhoubeh_NEW_JOBS_TOPIC_ID)):
        
        user_info = f"{message.from_user.username if message.from_user.username else message.from_user.first_name}"
        logger.info(f"📥 رسالة جديدة من {user_info} في توبيك الوظائف: {message.message_id}")
        
        # إضافة زر تحت الرسالة
        try:
            await message.reply_text(
                "👇",
                reply_markup=APPLY_BUTTON,
                message_thread_id=message.message_thread_id,
                reply_to_message_id=message.message_id
            )
            logger.info(f"✅ تم إضافة زر للرسالة: {message.message_id}")
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة الزر: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة ضغطات الأزرار"""
    
    query = update.callback_query
    await query.answer()
    
    # الحصول على معلومات المستخدم الذي ضغط على الزر
    user = query.from_user
    user_name = f"@{user.username}" if user.username else user.first_name
    user_id = user.id
    
    logger.info(f"🎯 زر مضغوط بواسطة {user_name} (ID: {user_id})")
    
    original_message = query.message.reply_to_message
    
    if not original_message:
        logger.warning("⚠️ لم يتم العثور على الرسالة الأصلية")
        await query.edit_message_text("❌ تعذر العثور على الرسالة")
        return
    
    if query.data == "move_to_applied":
        logger.info(f"📝 طلب تأكيد من {user_name} للرسالة {original_message.message_id}")
        await query.edit_message_text(
            f"⚠️ **{user_name}، هل أنت متأكد من انتهاء التقديم؟**",
            reply_markup=CONFIRM_KEYBOARD
        )
    
    elif query.data == "confirm_move":
        try:
            logger.info(f"🔄 بدء نقل الرسالة {original_message.message_id} بواسطة {user_name}")
            
            # 📌 نقل النص مع إضافة اسم المستخدم
            if original_message.text:
                await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID,
                    text=f"✅ تم التقديم بواسطة: {user_name}\n\n{original_message.text}",
                    message_thread_id=APPLIED_JOBS_TOPIC_ID
                )
                logger.info(f"📝 تم نقل رسالة نصية: {original_message.message_id}")
            
            # 📌 نقل الصور مع إضافة اسم المستخدم
            elif original_message.photo:
                caption = original_message.caption if original_message.caption else ""
                new_caption = f"✅ تم التقديم بواسطة: {user_name}\n\n{caption}"
                
                await context.bot.send_photo(
                    chat_id=GROUP_CHAT_ID,
                    photo=original_message.photo[-1].file_id,
                    caption=new_caption,
                    message_thread_id=APPLIED_JOBS_TOPIC_ID
                )
                logger.info(f"🖼️ تم نقل صورة: {original_message.message_id}")
            
            # 📌 نقل الملفات مع إضافة اسم المستخدم
            elif original_message.document:
                caption = original_message.caption if original_message.caption else ""
                new_caption = f"✅ تم التقديم بواسطة: {user_name}\n\n{caption}"
                
                await context.bot.send_document(
                    chat_id=GROUP_CHAT_ID,
                    document=original_message.document.file_id,
                    caption=new_caption,
                    message_thread_id=APPLIED_JOBS_TOPIC_ID
                )
                logger.info(f"📎 تم نقل ملف: {original_message.message_id}")
            
            # حذف الأصل
            await original_message.delete()
            logger.info(f"🗑️ تم حذف الرسالة الأصلية: {original_message.message_id}")
            
            # حذف رسالة التأكيد
            await query.message.delete()
            logger.info(f"🗑️ تم حذف رسالة التأكيد")
            
            logger.info(f"✅ تم نقل الرسالة {original_message.message_id} بنجاح بواسطة {user_name}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في نقل الرسالة {original_message.message_id}: {str(e)}")
            await query.edit_message_text(f"❌ خطأ: {str(e)[:100]}...")
    
    elif query.data == "cancel_move":
        logger.info(f"❌ تم إلغاء النقل من قبل {user_name}")
        await query.edit_message_text(
            "👇",
            reply_markup=APPLY_BUTTON
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأخطاء"""
    error_msg = str(context.error) if context.error else "خطأ غير معروف"
    # لا نسجل الأخطاء الروتينية من httpx
    if 'httpx' not in error_msg.lower() and 'http' not in error_msg.lower():
        logger.error(f"⚠️ خطأ في النظام: {error_msg}")
        
        # تسجيل تفاصيل إضافية عن الخطأ
        if update:
            if update.effective_message:
                logger.error(f"📝 تفاصيل الرسالة: {update.effective_message.message_id}")
            if update.effective_user:
                logger.error(f"👤 المستخدم: {update.effective_user.username or update.effective_user.first_name}")




def ensure_webhook_registered(token: str, base_url: str, max_retries: int = 5) -> bool:
    """
    Ensure Telegram webhook is registered to base_url/token.
    Returns True if webhook is set to the expected URL.
    """
    logger = logging.getLogger(__name__)
    base_url = (base_url or "").rstrip("/")
    if not base_url:
        logger.error("WEBHOOK_URL is empty. Cannot register webhook.")
        print("ERROR: WEBHOOK_URL is empty. Please set WEBHOOK_URL environment variable.")
        sys.stdout.flush()
        return False

    full_url = f"{base_url}/{token}"
    api_base = f"https://api.telegram.org/bot{token}"

    # Diagnostic print
    print("DEBUG: full webhook URL =", full_url)
    sys.stdout.flush()
    logger.info("DEBUG: full webhook URL = %s", full_url)

    # Check current webhook
    try:
        r = requests.get(f"{api_base}/getWebhookInfo", timeout=10)
        logger.info("getWebhookInfo: %s", r.text)
    except Exception as e:
        logger.warning("getWebhookInfo failed: %s", e)
        r = None

    current_url = None
    try:
        if r and r.ok:
            current_url = r.json().get("result", {}).get("url")
    except Exception:
        current_url = None

    if current_url == full_url:
        logger.info("Webhook already set to %s", full_url)
        print(f"✅ Webhook already set to {full_url}")
        sys.stdout.flush()
        return True

    # Try to set webhook with retries
    for attempt in range(1, max_retries + 1):
        try:
            logger.info("Setting webhook to %s (attempt %d)", full_url, attempt)
            resp = requests.post(f"{api_base}/setWebhook", data={"url": full_url}, timeout=10)
            logger.info("setWebhook response: %s", resp.text)
            print("setWebhook response:", resp.status_code, resp.text)
            sys.stdout.flush()
            if resp.ok and resp.json().get("ok"):
                logger.info("Webhook registered successfully")
                print(f"✅ Webhook registered successfully: {full_url}")
                sys.stdout.flush()
                return True
        except Exception as exc:
            logger.warning("setWebhook attempt %d failed: %s", attempt, exc)

        time.sleep(2 * attempt)

    logger.error("Failed to register webhook after %d attempts", max_retries)
    print(f"ERROR: Failed to register webhook after {max_retries} attempts")
    sys.stdout.flush()
    return False






def main():
    def main():
    # existing startup logs and cleanup
    print("🧹 جاري تنظيف الملفات القديمة...")
    clean_old_logs(days_to_keep=60)

    print("=" * 70)
    print("🚀 بوت نقل الوظائف - معدل لـ Render (Webhook)")
    print("=" * 70)

    application = None
    webhook_base = os.environ.get("WEBHOOK_URL", "")
    token = TOKEN  # ensure TOKEN is defined earlier from env

    try:
        # Build application and register handlers (synchronous)
        application = Application.builder().token(token).build()

        # Register your handlers here (example)
        application.add_handler(MessageHandler(filters.Chat(chat_id=GROUP_CHAT_ID) & ~filters.COMMAND, handle_new_job))
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_callback))
        application.add_error_handler(error_handler)

        # Ensure webhook is registered BEFORE starting the server
        ok = ensure_webhook_registered(token, webhook_base)
        if not ok:
            logger.warning("Webhook registration failed; continuing to run so you can inspect logs.")

        logger.info("Calling run_webhook (this will block until shutdown)")
        # Blocking call: do NOT await this
        application.run_webhook(
            listen="0.0.0.0",
            port=int(os.environ.get("PORT", 8080)),
            url_path=token,
            webhook_url=(webhook_base.rstrip("/") + "/" + token) if webhook_base else None
        )

        logger.info("run_webhook returned; application shutting down")

    except Exception as e:
        logger.critical(f"💥 فشل تشغيل البوت: {e}")
        traceback.print_exc()
        print(f"💥 خطأ حرج: {e}")
        sys.stdout.flush()

    finally:
        # run_webhook blocks until shutdown; when it returns, ensure cleanup
        if application is not None:
            try:
                if getattr(application, "running", False):
                    application.shutdown()
                    application.stop()
                    logger.info("✅ Application shutdown completed")
            except Exception as shutdown_exc:
                logger.warning(f"⚠️ خطأ أثناء الإغلاق: {shutdown_exc}")
                traceback.print_exc()


if __name__ == "__main__":
    main()










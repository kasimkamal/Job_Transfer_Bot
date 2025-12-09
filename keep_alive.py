from flask import Flask
from threading import Thread
import time
import requests

app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# دالة إضافية لزيارة نفس الخادم كل 5 دقائق (حل بديل مزدوج)
def ping_self():
    while True:
        time.sleep(300) # انتظر 300 ثانية = 5 دقائق
        try:
            requests.get("https://اسم_مشروعك.اسم_مستخدمك.repl.co") # ستغير هذا لاحقاً
        except:
            pass
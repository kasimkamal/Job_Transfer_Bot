# bot_min.py
import asyncio, os, sys
print("=== MINIMAL STARTUP TEST ===")
print("Python:", sys.version.replace("\n", " "))
try:
    import telegram
    print("telegram module file:", getattr(telegram, "__file__", "unknown"))
    print("telegram.__version__:", getattr(telegram, "__version__", "unknown"))
except Exception as e:
    print("Failed to import telegram:", e)
    sys.exit(1)

from telegram.ext import Application

async def main():
    print("Building Application...")
    app = Application.builder().token(os.environ.get("TELEGRAM_BOT_TOKEN", "dummy")).build()
    print("Application built:", type(app))
    # don't run webhook here; just build and exit
    await asyncio.sleep(1)
    print("MINIMAL TEST OK")

if __name__ == "__main__":
    asyncio.run(main())

"""
Achille — Sender
Envoie des messages proactifs via Telegram.
Utilisé par le scheduler pour les briefings, check-ins, etc.
"""
import asyncio
from telegram import Bot
from config.settings import TELEGRAM_BOT_TOKEN, AXEL_CHAT_ID

bot = Bot(token=TELEGRAM_BOT_TOKEN)


async def send(text: str, chat_id: int = AXEL_CHAT_ID) -> bool:
    """Envoie un message texte via Telegram."""
    try:
        # Découper si > 4096 chars
        for i in range(0, len(text), 4000):
            chunk = text[i:i+4000]
            await bot.send_message(chat_id=chat_id, text=chunk)
        return True
    except Exception as e:
        print(f"[sender error] {e}")
        return False


def send_sync(text: str, chat_id: int = AXEL_CHAT_ID) -> bool:
    """Version synchrone pour appel depuis le scheduler."""
    try:
        loop = asyncio.new_event_loop()
        result = loop.run_until_complete(send(text, chat_id))
        loop.close()
        return result
    except Exception as e:
        print(f"[sender_sync error] {e}")
        return False

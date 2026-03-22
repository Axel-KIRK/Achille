"""
Achille — Telegram Handler
Gère les messages entrants et orchestre le pipeline.
"""
import asyncio
import sqlite3
from datetime import datetime
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application, MessageHandler, CommandHandler, 
    ContextTypes, filters
)

from config.settings import TELEGRAM_BOT_TOKEN, AXEL_CHAT_ID, BRAIN_REPO_PATH
from brain.classifier import classify
from brain.context_assembler import build
from brain.responder import generate
from brain.dual_prompt import run as dual_prompt_run
from brain.sycophancy_guard import check as sycophancy_check
from memory.extractor import extract_and_update

# SQLite pour l'historique de conversation
DB_PATH = Path(BRAIN_REPO_PATH).parent / "achille_history.db"


def init_db():
    """Initialise la base SQLite pour l'historique."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT,
            role TEXT,
            content TEXT,
            timestamp TEXT,
            subject TEXT,
            layer INTEGER
        )
    """)
    conn.commit()
    conn.close()


def get_conversation_id() -> str:
    """Un ID de conversation par jour (reset chaque jour)."""
    return datetime.now().strftime("%Y-%m-%d")


def save_message(role: str, content: str, subject: str = "", layer: int = 0):
    """Sauvegarde un message dans l'historique."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, timestamp, subject, layer) VALUES (?, ?, ?, ?, ?, ?)",
        (get_conversation_id(), role, content, datetime.now().isoformat(), subject, layer)
    )
    conn.commit()
    conn.close()


def get_recent_messages(limit: int = 10) -> list[dict]:
    """Récupère les derniers messages de la conversation du jour."""
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id DESC LIMIT ?",
        (get_conversation_id(), limit)
    ).fetchall()
    conn.close()
    
    # Inverser pour avoir l'ordre chronologique
    messages = [{"role": r[0], "content": r[1]} for r in reversed(rows)]
    return messages


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler principal pour les messages texte."""
    
    # Sécurité : seul Axel peut parler au daemon
    if update.effective_chat.id != AXEL_CHAT_ID:
        await update.message.reply_text("Ce daemon est privé.")
        return
    
    user_message = update.message.text
    if not user_message:
        return
    
    # Indicateur de frappe
    await context.bot.send_chat_action(chat_id=AXEL_CHAT_ID, action="typing")
    
    try:
        # 1. Classifier
        classification = await classify(user_message)
        
        # 2. Historique récent
        history = get_recent_messages()
        
        # 3. Assembler le contexte
        full_context = build(classification, history)
        
        # 4. Dual-prompt si conviction forte sur C2-C3
        dual_prompt_result = None
        if classification.get("is_strong_conviction") and classification.get("layer", 1) >= 2:
            dual_prompt_result = await dual_prompt_run(user_message)
        
        # 5. Générer la réponse
        if dual_prompt_result:
            # Injecter la synthèse dual-prompt comme contexte additionnel
            full_context["messages"].append({
                "role": "user",
                "content": f"<dual_prompt_analysis>\n{dual_prompt_result}\n</dual_prompt_analysis>\nIntègre cette analyse dans ta réponse de manière naturelle."
            })
            full_context["messages"].append({
                "role": "assistant",
                "content": "Compris, j'intègre les contre-arguments."
            })
        
        response = await generate(full_context, user_message)
        
        # 6. Sycophancy check
        conversation_id = get_conversation_id()
        response = sycophancy_check(response, conversation_id)
        
        # 7. Envoyer
        # Telegram limite à 4096 chars — découper si nécessaire
        for i in range(0, len(response), 4000):
            chunk = response[i:i+4000]
            await update.message.reply_text(chunk)
        
        # 8. Sauvegarder dans l'historique
        save_message("user", user_message, classification.get("subject"), classification.get("layer"))
        save_message("assistant", response, classification.get("subject"), classification.get("layer"))
        
        # 9. Post-traitement async
        asyncio.create_task(
            extract_and_update(user_message, response, classification)
        )
    
    except Exception as e:
        print(f"[handle_message error] {e}")
        await update.message.reply_text(f"Erreur interne. ({type(e).__name__})")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler pour les messages vocaux — transcription via Whisper."""
    if update.effective_chat.id != AXEL_CHAT_ID:
        return
    
    await context.bot.send_chat_action(chat_id=AXEL_CHAT_ID, action="typing")
    
    try:
        # Télécharger le fichier vocal
        voice = await context.bot.get_file(update.message.voice.file_id)
        voice_path = Path("/tmp/achille_voice.ogg")
        await voice.download_to_drive(str(voice_path))
        
        # Transcrire (import ici pour ne pas bloquer si pas installé)
        from bot.voice import transcribe
        text = await transcribe(voice_path)
        
        if text:
            # Simuler un message texte
            update.message.text = text
            await handle_message(update, context)
        else:
            await update.message.reply_text("Transcription échouée. Réessaie.")
    
    except Exception as e:
        print(f"[handle_voice error] {e}")
        await update.message.reply_text("Erreur lors de la transcription.")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /start."""
    if update.effective_chat.id != AXEL_CHAT_ID:
        await update.message.reply_text("Ce daemon est privé.")
        return
    
    await update.message.reply_text(
        "Achille est en ligne. Parle-moi."
    )


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Commande /status — état du système."""
    if update.effective_chat.id != AXEL_CHAT_ID:
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    today_count = conn.execute(
        "SELECT COUNT(*) FROM messages WHERE conversation_id = ? AND role = 'user'",
        (get_conversation_id(),)
    ).fetchone()[0]
    total_count = conn.execute("SELECT COUNT(*) FROM messages WHERE role = 'user'").fetchone()[0]
    conn.close()
    
    status = (
        f"Messages aujourd'hui : {today_count}\n"
        f"Messages total : {total_count}\n"
        f"Conversation ID : {get_conversation_id()}"
    )
    await update.message.reply_text(status)


def create_app(post_init_callback=None) -> Application:
    """Crée l'application Telegram."""
    init_db()

    builder = Application.builder().token(TELEGRAM_BOT_TOKEN)
    if post_init_callback:
        builder = builder.post_init(post_init_callback)
    app = builder.build()
    
    # Handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("status", cmd_status))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    return app

"""
Achille — Error Notification
Envoie les erreurs critiques à Axel sur Telegram.
"""
import traceback
from bot.sender import send


async def notify_error(context: str, error: Exception, verbose: bool = True):
    """Envoie une notification d'erreur sur Telegram.

    Args:
        context: d'où vient l'erreur (ex: "consolidation.dedup", "heartbeat.morning")
        error: l'exception
        verbose: inclure le traceback complet
    """
    try:
        msg = f"⚠ Erreur [{context}]\n{type(error).__name__}: {error}"
        if verbose:
            tb = traceback.format_exc()
            # Garder les 10 dernières lignes du traceback max
            tb_lines = tb.strip().splitlines()
            if len(tb_lines) > 10:
                tb_lines = tb_lines[-10:]
            msg += f"\n\n```\n{''.join(l + chr(10) for l in tb_lines)}```"
        # Tronquer si trop long pour Telegram
        if len(msg) > 3500:
            msg = msg[:3500] + "\n[tronqué]"
        await send(msg)
    except Exception:
        # Si même l'envoi Telegram échoue, on print en dernier recours
        print(f"[notify_error FAILED] {context}: {error}")


def notify_error_sync(context: str, error: Exception):
    """Version sync pour les contextes non-async. Log seulement (pas de Telegram)."""
    print(f"[{context}] {type(error).__name__}: {error}")

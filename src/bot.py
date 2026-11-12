import asyncio
import logging

from telegram import BotCommand, InputFile, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.config import Settings
from src.ponto import registrar_ponto

log = logging.getLogger("bot")

AJUDA = (
    "Comandos:\n"
    "/bater — registra o ponto agora\n"
    "/bater 12345 — registra numa matrícula específica\n"
    "/hoje — mostra o que está na tela de ponto, sem registrar\n"
    "/id — mostra seu id do Telegram\n"
    "/ajuda — esta mensagem"
)


def build_app(settings: Settings) -> Application:
    trava = asyncio.Lock()
    app = Application.builder().token(settings.telegram_token).post_init(_avisar_online(settings)).build()
    app.bot_data["settings"] = settings
    app.bot_data["trava"] = trava

    for nome in ("start", "ajuda", "help"):
        app.add_handler(CommandHandler(nome, _ajuda))
    app.add_handler(CommandHandler("id", _id))
    for nome in ("bater", "ponto", "registrar"):
        app.add_handler(CommandHandler(nome, _bater))
    app.add_handler(CommandHandler("hoje", _hoje))
    return app


def _avisar_online(settings: Settings):
    async def post_init(app: Application) -> None:
        await app.bot.set_my_commands(
            [
                BotCommand("bater", "Registra o ponto agora"),
                BotCommand("hoje", "Mostra os registros de hoje"),
                BotCommand("ajuda", "Lista os comandos"),
            ]
        )
        for chat_id in settings.allowed_ids:
            try:
                await app.bot.send_message(chat_id, "Bot do ponto online. Manda /bater quando quiser registrar.")
            except Exception:
                log.warning("não avisei o chat %s (a pessoa precisa mandar /start antes)", chat_id)

    return post_init


async def _ajuda(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await _liberado(update, context):
        return
    usuario = update.effective_user
    texto = AJUDA
    if usuario:
        texto += f"\n\nSeu id: {usuario.id}"
    await update.effective_message.reply_text(texto)


async def _id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    usuario = update.effective_user
    if usuario is None or update.effective_message is None:
        return
    settings: Settings = context.application.bot_data["settings"]
    if settings.allowed_ids and usuario.id not in settings.allowed_ids:
        await update.effective_message.reply_text("Esse Telegram não está autorizado.")
        return
    await update.effective_message.reply_text(f"Seu id é {usuario.id}.")


async def _bater(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _executar(update, context, apenas_consulta=False)


async def _hoje(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _executar(update, context, apenas_consulta=True)


async def _executar(update: Update, context: ContextTypes.DEFAULT_TYPE, *, apenas_consulta: bool) -> None:
    if not await _liberado(update, context):
        return
    mensagem = update.effective_message
    if mensagem is None:
        return

    settings: Settings = context.application.bot_data["settings"]
    trava: asyncio.Lock = context.application.bot_data["trava"]
    matricula = context.args[0] if context.args else None

    if trava.locked():
        await mensagem.reply_text("Ainda estou no portal. Espera esse terminar.")
        return

    aviso = "Vou abrir o portal e olhar os registros de hoje." if apenas_consulta else "Vou registrar o ponto. Leva alguns segundos."
    await mensagem.reply_text(aviso)
    await mensagem.chat.send_action("typing")

    async with trava:
        resultado = await registrar_ponto(settings, matricula, apenas_consulta=apenas_consulta)

    if resultado.screenshot:
        legenda = resultado.message[:1000]
        await mensagem.reply_photo(InputFile(resultado.screenshot, filename="ponto.png"), caption=legenda)
        if len(resultado.message) > 1000:
            await mensagem.reply_text(resultado.message)
        return
    await mensagem.reply_text(resultado.message[:4000])


async def _liberado(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    usuario = update.effective_user
    mensagem = update.effective_message
    chat = update.effective_chat
    if usuario is None or mensagem is None or chat is None:
        return False
    if chat.type != "private":
        return False

    settings: Settings = context.application.bot_data["settings"]
    if not settings.allowed_ids:
        await mensagem.reply_text(
            f"Seu id é {usuario.id}. Coloca ele em TELEGRAM_ALLOWED_IDS no .env "
            "e recria o container: docker compose up -d --force-recreate"
        )
        return False
    if usuario.id not in settings.allowed_ids:
        await mensagem.reply_text("Esse Telegram não está autorizado.")
        return False
    return True

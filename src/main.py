import logging
import time

from src.bot import build_app
from src.config import load_settings

log = logging.getLogger("main")


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    settings = load_settings()
    faltando = settings.missing()
    if faltando:
        log.error("Preencha no .env: %s", ", ".join(faltando))
        log.error("Depois rode: docker compose up -d --force-recreate")
        while True:
            time.sleep(3600)

    log.info("bot do ponto iniciando")
    build_app(settings).run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

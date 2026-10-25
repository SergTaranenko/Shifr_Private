"""Точка входа: python main.py"""
import logging

from advisor.bot import build_app
from advisor.config import load_config


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    cfg = load_config()
    app = build_app(cfg)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()

import sys
from argparse import Namespace

from icecream import ic as _ic
from loguru import logger

LOG_CONSOLE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <5}</level> | "
    "<cyan>{name}</cyan> - "
    "<level>{message}</level>"
)

LOG_FILE_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "{process: >6} | "
    "<level>{level: <5}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def log_to_loguru(s: str) -> None:
    logger.debug(s)


def enable_icecream(prefix: str = "") -> None:
    _ic.configureOutput(prefix=prefix, outputFunction=log_to_loguru)


def setup_logging(args: Namespace) -> None:
    enable_icecream()
    if args.quiet:
        level = "WARNING"
    elif args.debug:
        level = "DEBUG"
    else:
        level = "INFO"
    handlers = [
        dict(
            sink=sys.stderr,
            level=level,
            backtrace=False,
            diagnose=False,
            format=LOG_CONSOLE_FORMAT,
        ),
    ]
    if args.log_root is not None:
        handlers.append(
            dict(
                sink=args.log_root / "debug.log",
                mode="a",
                level=0,
                backtrace=False,
                diagnose=False,
                rotation="10 MB",
                compression="bz2",
                retention=3,
                enqueue=True,
                format=LOG_FILE_FORMAT,
            ),
        )
    logger.configure(handlers=handlers)


# XXX this explicit export is to make mypy happy
ic = _ic

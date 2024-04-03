from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, Namespace
from pathlib import Path

from loguru import logger

from . import __version__ as VERSION
from .generate import generate
from .log import setup_logging

HELP_FORMATTER = ArgumentDefaultsHelpFormatter


def parse_args() -> Namespace:
    parser = ArgumentParser("restic-backup-wrapper-cli", formatter_class=HELP_FORMATTER)
    parser.add_argument("--version", action="version", version=VERSION)
    parser.add_argument("-q", "--quiet", action="store_true", help="Log less")
    parser.add_argument("-d", "--debug", action="store_true", help="Log more")
    parser.add_argument(
        "-l",
        "--log-root",
        help="Log root path (specify '' to suppress logging to a file)",
        type=lambda s: Path(s) if s else None,
        metavar="PATH",
        default="logs",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    parse_command = commands.add_parser(
        "generate",
        formatter_class=HELP_FORMATTER,
        help="Parse data",
        description="Parse data from input",
    )
    parse_command.add_argument(
        "-i",
        "--input-file",
        help="Input TOML file",
        type=Path,
        metavar="PATH",
        required=True,
    )

    return parser.parse_args()


DISPATCH = {
    "generate": generate,
}


def cli() -> None:
    args = parse_args()
    setup_logging(args)
    logger.debug("args={}", args)
    # handle the args
    DISPATCH[args.command](args)

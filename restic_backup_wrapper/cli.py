from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser, FileType, Namespace
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

    parser.add_argument(
        "-i",
        "--input-file",
        help="Input TOML file",
        type=Path,
        metavar="PATH",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="Output file; if not specified or -, it is stdout",
        type=FileType("w"),
        metavar="PATH|-",
    )
    parser.add_argument(
        "-n", "--dry-run", action="store_true", help="Generate dry run for restic backup"
    )

    return parser.parse_args()


def cli() -> None:
    args = parse_args()
    setup_logging(args)
    logger.debug("args={}", args)
    # handle the args
    generate(args)

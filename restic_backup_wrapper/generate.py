from argparse import Namespace

from loguru import logger


def generate(args: Namespace) -> None:
    logger.info("Parse command, args={}", args)

import re
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import tomli
from jinja2 import Environment, FileSystemLoader
from loguru import logger

from . import __version__ as VERSION
from .line_tag import OneLineExtension, OneLineShlexExtension
from .log import ic

# name as come from <_io.TextIOWrapper name='<stdout>' mode='w' encoding='utf-8'>
STDOUT_DISPLAY_NAME = "<stdout>"
RESTIC_COMMAND_DEFAULT = "restic"
THIS_DIR = Path(__file__).parent
TEMPLATE_NAME = "commands.tmpl"


def is_folder_config(d: Any) -> bool:
    try:
        d["dir"]
    except Exception:
        return False
    return True


def _merge_and_remove(key: str, a: Dict[str, Any], b: Dict[str, Any]) -> List[Any]:
    value_a: List[Any] = []
    value_b: List[Any] = []
    if key in a:
        value_a = a[key]
        del a[key]
    if key in b:
        value_b = b[key]
        del b[key]
    return sorted(set(value_a + value_b))


BackupInfo = Dict[str, Any]


def _normalize_keys(d):
    return {re.sub("-", "_", k): v for k, v in d.items()}


def _generate_command(
    global_settings: Dict[str, Any],
    key: str,
    value: Dict[str, Any],
    dry_run: bool = False,
) -> BackupInfo:
    # XXX make all variable names with underscore (restic-command => restic_command)
    settings = dict(global_settings)
    exclude = _merge_and_remove("exclude", settings, value)
    tags = _merge_and_remove("tags", settings, value)

    # make 'dir' relative to the global value
    relative_to = settings.get("relative_to")
    dest = Path(value["dir"])
    abs_path = dest.expanduser().absolute()
    if not dest.expanduser().exists():
        logger.warning(
            "Path {} does not exist, you may have a problem when actually running the command",
            dest,
        )
    if relative_to:
        try:
            value["dir"] = dest.relative_to(Path(relative_to))
        except ValueError as exc:
            logger.debug("{} -- ignoring", exc)
            relative_to = None

    tvars = _normalize_keys(
        {
            **settings,
            "exclude": exclude,  # they are sorted
            "key": key,
            **value,
            # XXX must be last to override settings
            "relative_to": relative_to,
            "dry_run": dry_run,
            "tags": tags,  # they are sorted
            "abs_path": abs_path,
        }
    )
    ic(key, tvars)
    return tvars


def _generate_commands(toml: Path, dry_run: bool = False) -> Dict[str, Any]:
    def _iter(global_settings) -> Iterable[Tuple[str, BackupInfo]]:
        for key, value in filter(lambda t: is_folder_config(t[1]), d.items()):
            yield key, _generate_command(global_settings, key, value, dry_run)

    logger.info("Reading {}", toml)
    with toml.open("rb") as inp:
        d = tomli.load(inp)
    logger.debug("d={}", d)
    global_settings = _normalize_keys(
        {key: value for key, value in d.items() if not is_folder_config(value)}
    )
    global_settings.setdefault("restic_command", RESTIC_COMMAND_DEFAULT)
    ic(global_settings)

    return {**global_settings, "all_commands": dict(_iter(global_settings))}


def remove_empty_lines(s: str) -> str:
    return "\n".join(re.split(r"[\n\r]{2,}", s))


def generate(args: Namespace) -> None:
    logger.info(
        "Writing to {}",
        args.output_file.name
        if (args.output_file and hasattr(args.output_file, "name"))
        else STDOUT_DISPLAY_NAME,
    )
    jinja = Environment(
        loader=FileSystemLoader(THIS_DIR), extensions=[OneLineExtension, OneLineShlexExtension]
    )
    jinja.filters.update({"repr": repr, "sorted": sorted})

    print(
        remove_empty_lines(
            jinja.get_template(TEMPLATE_NAME).render(
                **_generate_commands(args.input_file, args.dry_run),
                cli_info=f"restic-backup-wrapper-cli {VERSION}",
                utc_now=datetime.now(timezone.utc),
            )
        ),
        file=args.output_file,
    )

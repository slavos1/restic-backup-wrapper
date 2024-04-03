import re
from argparse import Namespace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import tomli
from jinja2 import Template
from loguru import logger

from .log import ic

# name as come from <_io.TextIOWrapper name='<stdout>' mode='w' encoding='utf-8'>
STDOUT_DISPLAY_NAME = "<stdout>"
RESTIC_COMMAND_DEFAULT = "restic"
COMMAND_TEMPLATE = """
{% if relative_to %}
(cd {{relative_to}} &&
{% endif %}

{{restic_command}}

{% if restic_repo %}
-r {{restic_repo}}
{% endif %}

backup {{ dir }}

{% if dry_run %}
--dry-run
{% endif %}

{% if group_by %}
--group-by '{{group_by}}'
{% endif %}

{% if tags %}
--tag '{{ tags|join(',') }}'
{% endif %}

{% for i in exclude %}
-e '{{i}}'
{% endfor %}

{% if relative_to %}){% endif %}
"""


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


def _generate_command(
    global_settings: Dict[str, Any],
    key: str,
    value: Dict[str, Any],
    dry_run: bool = False,
    template: str = COMMAND_TEMPLATE,
) -> str:
    # XXX make all variable names with underscore (restic-command => restic_command)
    settings = dict(global_settings)
    exclude = _merge_and_remove("exclude", settings, value)
    tags = _merge_and_remove("tags", settings, value)

    # make 'dir' relative to the global value
    relative_to = settings.get("relative-to")
    dest = Path(value["dir"])
    if not dest.expanduser().exists():
        logger.warning(
            ("Path {} does not exist, you may have" " a problem when actually running the command"),
            dest,
        )
    if relative_to:
        try:
            value["dir"] = dest.relative_to(Path(relative_to))
        except ValueError as exc:
            logger.debug("{} -- ignoring", exc)
            relative_to = None

    tvars = {
        re.sub("-", "_", k): v
        for k, v in (
            {
                **settings,
                "exclude": exclude,  # they are sorted
                "key": key,
                **value,
                # XXX must be last to override settings
                "relative_to": relative_to,
                "dry_run": dry_run,
                "dest": dest,
                "tags": tags,  # they are sorted
            }.items()
        )
    }
    ic(tvars)
    return re.sub(
        "[ ]{2,}",
        " ",
        re.sub(
            "\n",
            " ",
            Template(
                template,
                trim_blocks=True,
                keep_trailing_newline=False,
                lstrip_blocks=True,
            )
            .render(**tvars)
            .strip(),
        ),
    )


def _generate(toml: Path, dry_run: bool = False) -> Dict[str, str]:
    def _iter() -> Iterable[Tuple[str, str]]:
        logger.info("Reading {}", toml)
        with toml.open("rb") as inp:
            d = tomli.load(inp)
        logger.debug("d={}", d)
        global_settings = {key: value for key, value in d.items() if not is_folder_config(value)}
        global_settings.setdefault("restic-command", RESTIC_COMMAND_DEFAULT)
        ic(global_settings)
        for key, value in filter(lambda t: is_folder_config(t[1]), d.items()):
            yield key, _generate_command(global_settings, key, value, dry_run)

    return dict(_iter())


def generate(args: Namespace) -> None:
    logger.info("Writing to {}", args.output_file.name if args.output_file else STDOUT_DISPLAY_NAME)
    print(
        "\n".join(sorted(_generate(args.input_file, args.dry_run).values())), file=args.output_file
    )

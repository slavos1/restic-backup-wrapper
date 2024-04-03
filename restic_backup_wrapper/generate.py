import re
from argparse import Namespace
from pathlib import Path
from typing import Any

import tomli
from jinja2 import Template
from loguru import logger

from .log import ic

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

{% for i in exclude %}
-e '{{i}}'
{% endfor %}

{% if relative_to %}
)
{% endif %}

"""


def is_folder_config(d: Any) -> bool:
    try:
        return "dir" in d
    except Exception:
        return False


def _merge_and_remove(key, a, b):
    value_a = []
    value_b = []
    if key in a:
        value_a = a[key]
        del a[key]
    if key in b:
        value_b = b[key]
        del b[key]
    return sorted(set(value_a + value_b))


def _generate_command(global_settings, key, value, template: str = COMMAND_TEMPLATE) -> str:
    # XXX make all variable names with underscore (restic-command => restic_command)
    settings = dict(global_settings)
    exclude = _merge_and_remove("exclude", settings, value)

    # make 'dir' relative to the global value
    relative_to = settings.get('relative_to')
    if relative_to:
        try:
            value['dir'] = Path(value['dir']).relative_to(Path(relative_to))
        except ValueError as exc:
            logger.debug("{} -- ignoring", exc)
            relative_to = None

    tvars = {
        re.sub("-", "_", k): v
        for k, v in (
            {
                **settings,
                "exclude": exclude,
                "key": key,
                **value,
                # XXX must be last to override settings
                "relative_to": relative_to,
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


def _generate(toml: Path):
    def _iter():
        with toml.open("rb") as inp:
            d = tomli.load(inp)
        logger.debug("d={}", d)
        global_settings = {key: value for key, value in d.items() if not is_folder_config(value)}
        global_settings.setdefault("restic-command", RESTIC_COMMAND_DEFAULT)
        ic(global_settings)
        for key, value in filter(lambda t: is_folder_config(t[1]), d.items()):
            yield key, _generate_command(global_settings, key, value)

    return dict(_iter())


def generate(args: Namespace) -> None:
    logger.info("Parse command, args={}", args)

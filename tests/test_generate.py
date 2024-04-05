import re
from argparse import Namespace
from io import StringIO
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pytest

from restic_backup_wrapper.generate import _merge_and_remove, generate
from restic_backup_wrapper.log import ic


@pytest.fixture(params=["absolute", "relative"])
def toml(request: Any, tmp_path: Path) -> Dict[str, Union[Optional[Path], str]]:
    toml_file = tmp_path / "my_backup.toml"
    if request.param == "relative":
        relative_to = tmp_path / "my-home"
        relative_to.mkdir(parents=True, exist_ok=True)
    else:
        relative_to = ''
    unrelated_dir = tmp_path / "unrelated-source-dir"
    restic_repo: Path = tmp_path / "restic-repo"
    restic_repo.mkdir(parents=True, exist_ok=True)
    restic_repo.mkdir(parents=True, exist_ok=True)
    with toml_file.open("w") as out:
        print(
            f"""
restic-repo = "{restic_repo}"
relative-to = "{relative_to}"
group-by = "piffle,paddle"
# will be added to all backups
exclude = ['.git']

[relative-folder]
dir = "{relative_to}/my-folder-rel"
tags = ['tag-b','a tag with a space','tag-a']
exclude = [".hg"]
keep-last = 1

[absolute-folder]
dir = "{unrelated_dir}/my-folder-abs"
tags = ['abs-tag']

[non-exist]
dir = 'non-exit'

[no-tag]
dir = 'non-tag-folder'

          """,
            file=out,
        )
    return {"toml": toml_file, "relative_to": relative_to, "restic_repo": restic_repo}


def test_merge_and_remove() -> None:
    a = {"exclude": [1, 2]}
    b = {"other": "x"}
    assert _merge_and_remove("exclude", a, b) == [1, 2]
    assert a == {}
    assert "other" in b
    #
    a = {"exclude": [1, 2]}
    b = {"other": "x", "exclude": [2, 3]}
    assert _merge_and_remove("exclude", a, b) == [1, 2, 3]
    assert a == {}
    assert "other" in b
    assert "exclude" not in b


def assert_is_in_any(needle: str, haystack: List[str]) -> None:
    assert any(needle in command for command in haystack), f"{needle!r} in {haystack!r}"


def test_generate(toml) -> None:
    args = Namespace()
    args.input_file = toml["toml"]
    args.output_file = StringIO()
    args.dry_run = None

    generate(args)
    commands = args.output_file.getvalue()
    ic(commands)
    relative_to = toml["relative_to"]
    relative_flag = f"cd {relative_to} &&"
    commands_absolute_folder = re.findall(r"^.*my\-folder\-abs.*", commands, flags=re.MULTILINE)
    commands_relative_folder = re.findall(r"^.*my\-folder\-rel.*", commands, flags=re.MULTILINE)
    commands_no_tag = re.findall(r"^.*non\-tag\-folder.*", commands, flags=re.MULTILINE)[0]
    ic(commands_absolute_folder)
    assert relative_flag not in commands_absolute_folder[0]
    assert "-e .git -e .hg" in commands_relative_folder[0]
    assert "-e .git" in commands_absolute_folder[0]
    assert "-e .hg" not in commands_absolute_folder[0]
    assert re.search(r"--tag\s+'(.*?)'", commands_relative_folder[0]).group(1) == "a tag with a space,tag-a,tag-b"
    assert not re.search(r"--tag\s+", commands_no_tag)
    assert re.search(r"--group-by\s+piffle,paddle", commands_no_tag)
    assert "--keep-last 1" in commands_relative_folder[1]

    ic(commands_relative_folder)
    if relative_to:
        assert relative_flag in commands_relative_folder[0]
    else:
        assert relative_flag not in commands_relative_folder[0]

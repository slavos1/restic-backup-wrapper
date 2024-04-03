import re
from pathlib import Path
from typing import Any, Dict, Optional, Union

import pytest

from restic_backup_wrapper.generate import _generate, _merge_and_remove


@pytest.fixture(params=["absolute", "relative"])
def toml(request: Any, tmp_path: Path) -> Dict[str, Union[Optional[Path], str]]:
    toml_file = tmp_path / "my_backup.toml"
    if request.param == "relative":
        relative_to = tmp_path / "my-home"
        relative_to.mkdir(parents=True, exist_ok=True)
    else:
        relative_to = None
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
tags = ['tag-b','tag-a']
exclude = [".hg"]

[absolute-folder]
dir = "{unrelated_dir}/my-folder-abs"
tags = ['abs-tag']

[non-exist]
dir = 'non-exit'

[no-tag]
dir = 'non-exit'

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


def test_generate(toml) -> None:
    commands = _generate(toml["toml"])
    relative_to = toml["relative_to"]
    relative_flag = f"cd {relative_to}"
    assert relative_flag not in commands["absolute-folder"]
    assert "-e '.git' -e '.hg'" in commands["relative-folder"]
    assert "-e '.git'" in commands["absolute-folder"]
    assert "-e '.hg'" not in commands["absolute-folder"]
    assert re.search(r"--tag\s+'(.*?)'", commands["relative-folder"]).group(1) == "tag-a,tag-b"
    assert not re.search(r"--tag\s+", commands["no-tag"])
    assert re.search(r"--group-by\s+'piffle,paddle'", commands["no-tag"])

    if relative_to:
        assert relative_flag in commands["relative-folder"]
    else:
        assert relative_flag not in commands["relative-folder"]

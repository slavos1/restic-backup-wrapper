# restic-backup-wrapper readme

Use a custom config for many backups

## Prerequisites

* [`hatch`](https://hatch.pypa.io/) -- install via `pipx hatch` or `pip install --user hatch`

## Project organization

```
├── LICENSE
├── Makefile
├── coverage.cfg        <- setup for test coverage ('tox -e cov')
├── pyproject.toml      <- instead of setup.py, recognized by tox too
├── README.md           <- this file
├── tests
│   └── test_foo.py     <- write your own tests here
└── restic_backup_wrapper   <- your package files
    ├── __init__.py
    ├── ...
```

## How to use

```console
# run the CLI
hatch run cli
make cli

# run the CLI help
hatch run help
make help

# or append any CLI-defined args, like --help
hatch run cli --help
make cli EXTRA='...'

# run mypy
hatch run types:check
make mypy

# run tests
hatch run test

# go to the venv shell
hatch shell
```

## On restic and relative paths

According [the restic author](https://forum.restic.net/t/backing-up-restoring-relative-paths/744/2), restic keeps relative and absolute paths.
It is not obvious from `restic snaphots`, where absolute paths are shown; but running `restic ls <snapshot-id>` for snapshot backed up from a relative path, `/` is shown as the "parent" folder; not the full folder.
**So one should imagine how `tar` does it.**

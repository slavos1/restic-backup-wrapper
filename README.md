# restic-backup-wrapper tool

_Generated from [source_readme.adoc](source_readme.adoc)._

<!-- START doctoc generated TOC please keep comment here to allow auto update -->
<!-- DON'T EDIT THIS SECTION, INSTEAD RE-RUN doctoc TO UPDATE -->

- [Example](#example)
- [Syntax](#syntax)
- [Prerequisites](#prerequisites)
- [How to use](#how-to-use)
- [Local install and run](#local-install-and-run)
- [Input file format](#input-file-format)
  - [Global parameters](#global-parameters)
  - [Backed up folders](#backed-up-folders)
- [restic and relative paths](#restic-and-relative-paths)
- [Writing documentation](#writing-documentation)

<!-- END doctoc generated TOC please keep comment here to allow auto update -->


**restic-backup-wrapper-cli** is a command-line tool that generates
[`restic`](https://restic.readthedocs.io/en/latest/040_backup.html)
commands from a TOML config file.

The output is suitable for piping to a (Posix) shell. If you have the
`RESTIC_REPOSITORY` and `RESTIC_PASSWORD` environment variables set up
already, you can run it simply as:

``` shell
restic-backup-wrapper-cli -l '' -i my-backup.toml | bash -xs
```

<div class="caution">

*Please note although this script is provided in the hope it will be
[useful](LICENSE), use caution when running it. Always review the
generated `restic` commands, as improper use could potentially damage
your backup data.*

</div>

# Example

Given a [TOML file](min.toml) `min.toml`:

``` toml
# a sample config
relative-to = "/home/user"
group-by = "host,paths,tags"
# global exclude: will be added to all backups
exclude = ['.git', '*.py[cd]', '__pycache__']

[my-folder-one]
dir = "/home/user/my-folder-one"
tags = ['mobile', 'voice', 'audio']
exclude = ['.hg']

[folder-with-one-backup]
dir = "/home/user/readme.txt"
tags = ['doc']
keep-last = 1

[absolute-path]
dir = "/mnt/data"
tags = ['external']
```

then

``` shell
restic-backup-wrapper-cli -l '' -i min.toml
```

generates `restic` commands:

``` shell
# Generated by restic-backup-wrapper-cli 0.2.1 on ...
#
# commands for key 'my-folder-one'
#
(cd /home/user && restic backup my-folder-one --group-by host,paths,tags --tag audio,mobile,voice -e '*.py[cd]' -e .git -e .hg -e __pycache__)
#
# commands for key 'folder-with-one-backup'
#
(cd /home/user && restic backup readme.txt --group-by host,paths,tags --tag doc -e '*.py[cd]' -e .git -e __pycache__)
(cd /home/user && restic forget --prune --keep-last 1 --path /home/user/readme.txt)
#
# commands for key 'absolute-path'
#
restic backup /mnt/data --group-by host,paths,tags --tag external -e '*.py[cd]' -e .git -e __pycache__
```

# Syntax

``` text
usage: restic-backup-wrapper-cli [-h] [--version] [-q] [-d] [-l PATH] -i PATH
                                 [-o PATH|-] [-n]

options:
  -h, --help            show this help message and exit
  --version             show program's version number and exit
  -q, --quiet           Log less (default: False)
  -d, --debug           Log more (default: False)
  -l PATH, --log-root PATH
                        Log root path (specify '' to suppress logging to a
                        file) (default: logs)
  -i PATH, --input-file PATH
                        Input TOML file (default: None)
  -o PATH|-, --output-file PATH|-
                        Output file; if not specified or -, it is stdout
                        (default: None)
  -n, --dry-run         Generate dry run for restic backup (default: False)
```

# Prerequisites

  - [`hatch`](https://hatch.pypa.io/) — install via `pipx hatch` or `pip
    install --user hatch`

# How to use

``` shell
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
make
hatch run test

# go to the venv shell
hatch shell

# write documentation
make doc

# increase version
hatch version <new-version>
```

# Local install and run

``` shell
rm -rf dist/
hatch build
pipx install dist/*.whl
restic-backup-wrapper-cli --version
restic-backup-wrapper-cli --help

# or you can use
make local
```

# Input file format

`-i`/`--input-file` is a TOML file of the following format.

## Global parameters

  - `restic-repo` (optional)  
    If specified, `restic -r <restic-repo>` will be generated. If not
    specified `-r XXX` will omitted. I do not use this flag as my
    `restic` is actually a custom alias/wrapper that sets my restic repo
    password as an environment variable.

  - `relative-to` (optional)  
    If specified, all `dir` paths (see below) that are relative to this
    path will be backed up as relative.
    
    <div class="informalexample">
    
    If `relative-to="X"` and a `dir="X/Y"` then the generated command
    will be `(cd X && restic backup Y …​)`.
    
    </div>

  - `group-by` (optional)  
    Translates to `--group-by` restic flag. It will be omitted from the
    generated command if not specified.

  - `exclude` (optional)  
    Add these exclude patterns to every generated command. The
    folder-specific excludes will be merged with this exclude, if any.

## Backed up folders

Each key of the form `[my-dir]` represents a folder to be backed up and
for which a `restic backup` command will be generated.

<div class="tip">

The key can be an arbitrary string and does not need to match
folder/file being backup up.

</div>

For each such entry, `restic-backup-wrapper-cli` recognizes these
parameters:

  - `dir` (mandatory)  
    Path to back up; if `relative-to` is set in the global parameters to
    a path `X`, `dir` will end up backed up as relative to `X` if it is
    a descendant path of `X`; otherwise it is kept as is.

  - `tags` (optional)  
    A list of tags; tags `['x','a tag with space']` will end up as
    `restic backup …​ --tag 'a tag with space,x' …​` (spaces in the tags
    are allowed).

  - `exclude` (optional)  
    Exclude patterns relevant to this folder. These patterns, if any,
    will be merged with the global `exclude`.

  - `keep-last` (optional; added in version `0.2.0`)  
    Generate *another* line to keep only the specified number of
    snapshots, something like `restic …​ forget --prune --keep-last <N>
    --path <full-folder-path>`.

# restic and relative paths

According to [the restic
author](https://forum.restic.net/t/backing-up-restoring-relative-paths/744/2),
restic keeps relative and absolute paths. It is not obvious from `restic
snaphots` where only absolute paths are shown. Running `restic ls
<snapshot-id>` for a snapshot backed up from a relative path will show
`/` as the "parent" path (and not the full path).

*So one should imagine how `tar` does it.*

# Writing documentation

When writing documentation, edit `source_readme.adoc`, run `make
doc-devel` and preview the generated `readme.html`.

Once ready to commit, run `make doc` to generate [README.md](README.md)
file from [source\_readme.adoc](source_readme.adoc) (and included
files).

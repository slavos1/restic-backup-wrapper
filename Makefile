HATCH=hatch

all: test

cli test cov help:
	${HATCH} run $@ ${EXTRA}

# XXX always run formatter first to wrap long lines
# https://github.com/pypa/hatch/discussions/1205#discussioncomment-8087562
fmt:
	${HATCH} fmt -f
	${HATCH} fmt
	
mypy:
	${HATCH} run types:check

build:
	${HATCH} build

min:
	${HATCH} run cli -l '' -d -i min.toml -o min.sh

gen:
	${HATCH} run cli -l '' -q -i ~/my_shell_home/bin/backup.toml

# local install
local:
	-rm -rf dist/
	hatch build
	pipx install --force dist/*.whl
	restic-backup-wrapper-cli --version

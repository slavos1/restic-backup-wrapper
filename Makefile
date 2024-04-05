HATCH=hatch
SHELL=bash

.PHONY: README.md readme.docbook

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

min.sh::
	${HATCH} run cli -i min.toml| sed '/^\s*$$/d' > $@.tmp
	mv $@.tmp $@

help.txt::
	${HATCH} run cli --help 2>&1 > $@.tmp
	mv $@.tmp $@

define adoc
	asciidoctor -a toc=left -a min-sh=min.sh -a doc-help=help.txt ${2} -o ${1} readme.adoc
endef

doc-html: min.sh help.txt
	$(call adoc,readme.html)

doc-devel:
	chokidar --initial '*.adoc' 'min.toml' Makefile -c '${MAKE} doc-html'

readme.docbook:
	$(call adoc,readme.docbook,-b docbook)

README.md: readme.docbook
	echo -e "_Generated from [readme.adoc](readme.adoc)._\n\n" > $@.tmp
	pandoc -f docbook -t gfm $< -o - >> $@.tmp
	mv $@.tmp $@

doc-md: README.md

doc: doc-html doc-md

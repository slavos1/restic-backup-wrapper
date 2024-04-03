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

# Make sure to: pip install twine
# https://github.com/pypa/twine

PACKAGE=emrt.necd.content

VERSION=$(shell grep "VERSION = " setup.py | grep -o '[0-9.]*')

all:

build:
	./build_manylinux.sh

release: build
	twine upload ./dist/${PACKAGE}-${VERSION}-*.whl
	twine upload ./dist/${PACKAGE}-${VERSION}-*.egg

clean:
	rm -rf build/ dist/

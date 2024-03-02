# -----------------------------------------------------------------------------
# Makefile for RACE in the Box
#
# Commands:
# help                        Print help documentation
# black                       Run Python's Black formatter on the code
# build_image                 Build the RiB Docker Image
# build_package               Build the RiB Python Package (using setuptools)
# clean                       Clean Python Package Data (Tests/Eggs/Cache)
# install                     Install the python package locally for testing
# mypy                        Run Python's Mypy type checker on the code
# pylint                      Run Python's Pylint syntax checker on the code
# vulture                     Run Python's vulture dead code checker on the code
# test                        Test the python package (using setuptools and pytest)
# test_orchestration          Test orchestration items for RiB Are in compliance (e.g. shellcheck and versions)
# test_scripts                Run Unit Tests for scripts (pytest)
# test_unit                   Run Unit Tests (using setuptools and pytest
# todo                        Get project TODOs
#
# Example Call:
#    make build VERSION=0.9.0
# -----------------------------------------------------------------------------


###
# Variables
###


VERSION=`cat ./VERSION`


###
# Help/Setup
###


# Make phone commands
.PHONY: test build install clean todo

help:
	# Print help documentation
	@echo "This makefile holds the following targets"
	@echo "  help                        Print help documentation"
	@echo "  black                       Run Python's Black formatter on the code"
	@echo "  black_check                 Run Python's Black formatter on the code in check mode, fail if code is not compliant with Black's style (run in CI)"
	@echo "  build_image                 Build the RiB Docker image"
	@echo "  build_package               Build the RiB Python package (using setuptools)"
	@echo "  clean                       Clean Python package data (tests/eggs/cache)"
	@echo "  install                     Install the Python package locally for testing"
	@echo "  mypy                        Run Python's Mypy type checker on the code"
	@echo "  pycodestyle                 Run Pycodestyle on the package"
	@echo "  pylint                      Run Python's Pylint syntax checker on the code"
	@echo "  test                        Run unit tests (using setuptools and pytest) (same as test_unit)"
	@echo "  test_orchestration          Test orchestration items for RiB are in compliance (e.g. shellcheck and versions)"
	@echo "  test_scripts                Run unit tests for scripts (pytest)"
	@echo "  test_unit                   Run unit tests (using setuptools and pytest)"
	@echo "  todo                        Get project TODOs"


###
# Development/Standards Tools
###


todo:
	# Get all package TODOs
	grep -rE "TODO" rib | egrep .py | egrep -v .html | egrep -v .eggs | egrep -v .pyc

mypy:
	# Run Mypi on the package
	python3 -m mypy --config-file=.mypy.ini rib

pycodestyle:
	# Run Pycodestyle on the package
	python3 -m pycodestyle --config=.pycodestylerc rib

pylint:
	# Run Pylint on the package
	python3 -m pylint --rcfile=.pylintrc --fail-under=9 --disable=duplicate-code rib

pylint_dup:
	# Run Pylint on the package
	python3 -m pylint --rcfile=.pylintrc --enable=duplicate-code rib

pylint_errors:
	# Run Pylint on the package, get errors only
	python3 -m pylint --rcfile=.pylintrc --errors-only rib

pylint_report:
	# Run Pylint on the package, Build Report
	# Requires "python3 -m pip install pylint-json2html"
	mkdir -p reports/pylint/
	python3 -m pylint --rcfile=.pylintrc --output-format=json rib |  pylint-json2html -o reports/pylint/report.html

black:
	# Run Black on the package
	python3 -m black --config=.blackrc.toml rib

black_check:
	# Run Black on the package to see if files would change, but do not change them
	# Will fail if files are left to change (need to run make black)
	python3 -m black --config=.blackrc.toml --check rib

vulture:
	# Run vulture on the package
	python3 -m vulture --exclude "**/tests/*" rib/

###
# Test Steps
###


test: test_unit
	# Run all test steps

test_unit:
	# Run Unit Tests (using setuptools and pytest)
	python3 setup.py test --addopts="-m 'not integration'"

unit_test: test_unit

test_orchestration:
	# Testing Orchestration for the Project
	bash scripts/internal/test_rib_orchestration.sh


###
# Buid Process
###


build_package:
	# Build the RiB Python Package (using setuptools)
	python3 setup.py build

build_image:
	# Build the RiB Docker Image
	bash docker-image/build_race_in_the_box.sh --version="${VERSION}"


###
# Install
###


# Need to set SETUPTOOLS_USE_DISTUTILS=stdlib per the breaking change in v60.
# https://setuptools.pypa.io/en/latest/history.html#v60-0-0
# Without this env var set we were seeing this error:
#     Traceback (most recent call last):
#     File "/race_in_the_box/rib/scripts/internal/initialize_rib_state.py", line 21, in <module>
#         from rib.utils import rib_utils
#     ModuleNotFoundError: No module named 'rib'
install:
	SETUPTOOLS_USE_DISTUTILS=stdlib python3.8 -m pip install --editable .


###
# Cleanup Process
###


clean:
	# Clean Python Package Data (Tests/Eggs/Cache)
	rm -rf \
		*.DS_Store* \
		*.egg* \
		.eggs \
		.pytest_cache/ \
		.mypy_cache/ \
		reports/ \
		.coverage \
		build/
	find . -name '__pycache__' -type d | xargs rm -fr
	find . -name '*.pyc' -delete
	find . -name '*.pyo' -delete

#!/usr/bin/env bash

rm -rf ./dist ./morix.egg-info ./.pytest_cache ./build

python -m build
twine upload dist/*

rm -rf ./dist ./morix.egg-info ./.pytest_cache ./build
#!/bin/bash

rm -rf dist sierra.egg.info
cd docs && make man && cd ..
python3 -m build
python3 -m twine upload --repository testpypi dist/* --verbose

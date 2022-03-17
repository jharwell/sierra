#!/bin/bash
# $1 - The repository to upload to

rm -rf dist sierra.egg.info
cd docs && make man && cd ..
python3 -m build
python3 -m twine upload --repository $1 dist/* --verbose

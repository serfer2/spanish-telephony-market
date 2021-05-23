#!/bin/bash
set -e
flake8 . --exclude=migrations,settings,__init__.py,.venv,alembic --ignore=E501,E722,W605,W504

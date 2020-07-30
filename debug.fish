#!/usr/local/bin/fish
source canvas.fish.secret
pipenv3 run python3 -i source/main.py --log=INFO $argv

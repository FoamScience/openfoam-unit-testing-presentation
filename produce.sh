#!/usr/bin/bash
#manim --disable_caching -qh -p bayesian.py
set -e
source .venv/bin/activate
manim -qh -p ut.py
manim-slides convert --to html -c progress=true -c controls=true -cslide_number=true "UnitTesting" "UnitTesting.html"
./node_modules/html-inject-meta/cli.js < UnitTesting.html  > index.html

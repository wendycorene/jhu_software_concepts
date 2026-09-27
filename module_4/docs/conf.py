"""Sphinx configuration; importing application modules does not query the DB."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))

project = 'Grad Cafe Analytics'
author = 'Wendy Eloe'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.viewcode']
autodoc_member_order = 'bysource'
html_theme = 'alabaster'
exclude_patterns = ['_build']
root_doc = 'index'

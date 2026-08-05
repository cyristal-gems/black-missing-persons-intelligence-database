#!/usr/bin/env python3
"""Generate case Markdown files from the canonical CSV without rewriting JSON."""

import os
import runpy
from pathlib import Path


os.environ["DOCS_ONLY"] = "1"
runpy.run_path(
    str(Path(__file__).with_name("generate_assets.py")),
    run_name="__main__",
)

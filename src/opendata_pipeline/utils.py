"""This module contains some very minimal utility functions."""

from pathlib import Path
import shutil


def setup():
    """Setup the data directory."""
    Path("data").mkdir(exist_ok=True)


def teardown():
    """Remove the data directory and all of its files. Remove extracted drugs file."""
    p = Path("data")
    shutil.rmtree(p)
    Path("extracted_drugs.jsonl").unlink()

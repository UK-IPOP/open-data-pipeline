"""This module contains some very minimal utility functions."""

from pathlib import Path
import shutil
from rich.console import Console


console = Console()


def setup():
    """Setup the data directory."""
    console.log("Setting up data directory...")
    Path("data").mkdir(exist_ok=True)


def teardown():
    """Remove the data directory and all of its files. Remove extracted drugs file."""
    console.log("Tearing down data directory...")
    p = Path("data")
    shutil.rmtree(p)
    Path("extracted_drugs.jsonl").unlink()

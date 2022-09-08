from pathlib import Path
import shutil


def setup():
    Path("data").mkdir(exist_ok=True)


def teardown():
    p = Path("data")
    shutil.rmtree(p)
    Path("extracted_drugs.jsonl").unlink()

import geocoder
from opendata_pipeline import models

with open("data/san_diego_county.jsonl", "r") as f:
    for i, line in enumerate(f.readlines()):
        if i > 10:
            break
        record = models.SanDiego.parse_raw(line)

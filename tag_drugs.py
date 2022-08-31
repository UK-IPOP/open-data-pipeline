import json

with open("lookup_data.json", "r") as f:
    lookup = json.load(f)


with open("extracted_drugs.jsonl", "r") as f1:
    with open("tagged_drugs.jsonl", "w") as f2:
        for line in f1.readlines():
            result = json.loads(line)
            term = result["search_term"].lower()
            tags = lookup[term]
            del result["algorithm"]
            f2.write(json.dumps(result | {"tags": tags}) + "\n")

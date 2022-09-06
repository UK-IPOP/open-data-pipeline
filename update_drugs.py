import csv
import json
import models
from sqlmodel import SQLModel, create_engine, Session

with open("lookup_data.json", "r") as f:
    lookup = json.load(f)


with open("extracted_drugs.jsonl", "r") as drug_output:
    drugs = []
    for line in drug_output:
        drug_output = json.loads(line)
        drug_output["tags"] = lookup[drug_output["search_term"].lower()]
        drug = models.DrugRecord.parse_obj(drug_output)
        drugs.append(drug)


engine = create_engine(
    "postgresql://postgres:USA61kilos!@db.aesbbmdzdsvqzjjjtkrn.supabase.co:5432/postgres",
    echo=True,
)
SQLModel.metadata.create_all(engine)
with Session(engine) as session:
    session.add_all(drugs)
    session.commit()

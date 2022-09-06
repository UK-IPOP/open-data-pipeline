import csv
import models
from sqlmodel import Session, create_engine, SQLModel, select


def prepare_drug_input(
    records: list[models.SanDiegoCountyRecord | models.CookCountyRecord],
) -> list[models.DrugInput]:
    drug_inputs: list[models.DrugInput] = []
    for record in records:
        if type(record) == models.SanDiegoCountyRecord:
            id_ = record.row_number
            source = models.Source.SAN_DIEGO
        elif type(record) == models.CookCountyRecord:
            id_ = record.casenumber
            source = models.Source.COOK_COUNTY
        else:
            raise ValueError("Invalid record type")
        drug_inputs.append(
            models.DrugInput(
                case_identifier=id_,
                text=record.text_for_search(primary=True),
                data_source=source,
                is_primary=True,
            )
        )
        drug_inputs.append(
            models.DrugInput(
                case_identifier=id_,
                text=record.text_for_search(primary=False),
                data_source=source,
                is_primary=False,
            )
        )
    return drug_inputs


def drug_input_to_csv(data: list[models.DrugInput], filename: str):
    records = [d.dict() for d in data if d]
    with open(filename, "w") as f:
        csvwriter = csv.DictWriter(f, fieldnames=records[0].keys())
        csvwriter.writeheader()
        for record in records:
            csvwriter.writerow(record)


if __name__ == "__main__":
    # somehow get records
    sql_lite_db = "data/database.db"
    engine = create_engine(
        "postgresql://postgres:USA61kilos!@db.aesbbmdzdsvqzjjjtkrn.supabase.co:5432/postgres",
        echo=True,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        records1 = session.exec(select(models.SanDiegoCountyRecord)).all()
        records2 = session.exec(select(models.CookCountyRecord)).all()
        records = records1 + records2
        drug_inputs = prepare_drug_input(records)
        drug_input_to_csv(drug_inputs, "data/drug_input.csv")
        # then we run the drug tool
        # then we run the other python script

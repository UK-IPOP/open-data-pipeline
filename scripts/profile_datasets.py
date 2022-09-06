#TODO: make this into a bash script using pipx to install pandas-profling!
import pandas as pd
from pandas_profiling import ProfileReport
from pathlib import Path
from tqdm import tqdm

Path("reports").mkdir(exist_ok=True)

for datafile in tqdm(
    Path("data").glob("*.jsonl"), description="Profiling files...", transient=True
):
    df: pd.DataFrame = pd.read_json(datafile, lines=True)  # type: ignore
    report = ProfileReport(
        df,
        title=datafile.name.replace(".jsonl", "_report").replace("_", " ").title(),
        explorative=True,
    )
    report.to_file(Path(f"reports/{datafile.name.replace('.jsonl', '.html')}"))
    print(f"Wrote {datafile.name.strip('.jsonl')} to file.")

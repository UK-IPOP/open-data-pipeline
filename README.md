# Medical Examiner Open Data Pipeline

[![Pipeline](https://github.com/UK-IPOP/open-data-pipeline/actions/workflows/pipeline.yml/badge.svg?branch=main)](https://github.com/UK-IPOP/open-data-pipeline/actions/workflows/pipeline.yml)
[![Docs](https://github.com/UK-IPOP/open-data-pipeline/actions/workflows/pages/pages-build-deployment/badge.svg?branch=gh-pages)](https://github.com/UK-IPOP/open-data-pipeline/actions/workflows/pages/pages-build-deployment)

<img src="https://github.com/UK-IPOP/open-data-pipeline/assets/45318637/c5c50811-f242-42d2-adfd-fa5563c1a89f" alt="logo" width=500 />

This repository contains the code for the Medical Examiner Open Data Pipeline.

We currently fetch data from the following sources:

- [Cook County Medical Examiner's Archives](https://datacatalog.cookcountyil.gov/Public-Safety/Medical-Examiner-Case-Archive/cjeq-bs86)
- [San Diego Medical Examiner's Office](https://data.sandiegocounty.gov/Safety/Medical-Examiner-Cases/jkvb-n4p7)
- [Milwaukee County Medical Examiner's Office](https://county.milwaukee.gov/EN/Medical-Examiner)
- [Connecticut (State) Accidental Drug Deaths](https://data.ct.gov/Health-and-Human-Services/Accidental-Drug-Related-Deaths-2012-2022/rybz-nyjw/about_data)
- [Santa Clara County Medical Examiner's Office](https://data.sccgov.org/Health/Medical-Examiner-Coroner-Full-dataset/s3fb-yrjp/about_data)
- [Sacramento County Medical Examiner's Office](https://sacramentocounty.maps.arcgis.com/apps/dashboards/0661fb44435b4611bf52be84708c4591)
- [Pima County Medical Examiner's Office](https://www.google.com/url?sa=t&source=web&rct=j&opi=89978449&url=https://www.pima.gov/212/Medical-Examiner&ved=2ahUKEwidg83ljdqJAxWYwskDHdbRE4YQFnoECDkQAQ&usg=AOvVaw2T_hdJ3x-pqh07VFa9n6B8)

The results of this data are used in various other analysis here on GitHub:

- [Cook County](https://github.com/UK-IPOP/cook-county-analysis)
  - Where we add geospatial data to the Cook County data
    - This was excluded from this automated pipeline due to specific requirements for the data for only Cook County

## Getting Started

This repo exists mainly to take advantage of GitHub actions for automation.

The actions workflow is located in `.github/workflows/pipeline.yml` and is triggered weekly or manually.

This workflow fetches data from the configured data sources inside `config.json`, 
geocodes addresses (when available) using ArcGIS, extracts drugs using the drug extraction [toolbox](https://github.com/UK-IPOP/drug-extraction)
and then compiles and zips up the results into the GitHub Releases page.

The data is then available for download from the [releases page](https://github.com/UK-IPOP/open-data-pipeline/releases) page.

Further, the entire workflow effectively runs a series of commands using the CLI application `opendata-pipeline` which is located in the `src` directory.

This is also available via a docker image hosted on [ghcr.io](https://github.com/UK-IPOP/open-data-pipeline/pkgs/container/opendata-pipeline). The
benefits of using the CLI via a docker image is that you don't have to have Python or the drug toolbox on your local machine 🙂.

We utilize async methods to speed up the large number of web requests we make to the data sources.

> It is important to regularly fetch/pull from this repo to maintain an updated `config.json`

We currently do not guarantee Windows support unfortunately. If you want to help make that a reality, please submit a new [Pull Request](https://github.com/UK-IPOP/open-data-pipeline/pulls)

There is further API-documentation available on the GitHub Pages [website](https://uk-ipop.github.io/open-data-pipeline/) for this repo if you want to interact with the CLI.
I would recommend using the docker image as it is easier to use and always referring to the CLI `--help` for more information.

### Workflow

The workflow can best be described by looking at the `pipeline.yml` file.

<img width="1104" alt="CleanShot 2023-01-18 at 10 38 29@2x" src="https://user-images.githubusercontent.com/45318637/213240766-b9b26d7d-0a5a-409b-b363-be487b55a57f.png">

## Data Enhancements

The following table shows the fields that we **add** to the original datafiles:

| Column Name  | Description     |
| :------ | :------ |
| `CaseIdentifier` | A *unique* identifier *across all* the datasets. |
| `death_day` | Day of the Month death occurred  |
| `death_month`            | Month Name death occurred  |
| `death_month_num`        | Month Number death occurred  |
| `death_year`             | Year death occurred  |
| `death_day_of_week`      | Day of week death occurred. Starting with 0 on Monday.  Weekends are 5 (Saturday) & 6 (Sunday). |
| `death_day_is_weekend`   | Death occurred on weekend day  |
| `death_day_week_of_year` | Week of the year (of 52) that death occurred |
| `geocoded_latitude` | Geocoded latitude. |
| `geocoded_longitude` | Geocoded longitude. |
| `geocoded_score` | Confidence of geocoding. 70-100. |
| `geocoded_address`| The address that the geocoded results correspond to. Not the address provided to the geocoder. |


### Drug Columns

In addition to providing the extracted drugs as a separate file in each release, we also convert this data to wide-form for each dataset. This adds the following columns in the subsequent pattern:

| Column Name/Pattern | Description |
| :--- | :--- |
| `*_1` | `*` drug found in first search column provided in drug configuration |
| `*_2` | `*` drug found in second search column provided in drug configuration |
| `*_meta` | Drug of `*` category/class found in this record across _any_ search column.


## Requirements

- `uv`

## Installation

To install the python cli I recommend using [uv](https://github.com/astral-sh/uv).

```bash
uvx opendata-pipeline
```

To install the docker image, you can use the following command:

```bash
docker pull ghcr.io/uk-ipop/opendata-pipeline:latest
```

## Usage

Usage is very similar to any other command line application. The most important thing is to follow the workflow defined above.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Help me write some tests!

## License

[MIT](https://choosealicense.com/licenses/mit/)

## BibTex Citation

If you use this software or the enhanced data, please cite this repository:

```
@software{Anthony_Medical_Examiner_OpenData_2022,
  author = {Anthony, Nicholas},
  month = {9},
  title = {{Medical Examiner OpenData Pipeline}},
  url = {https://github.com/UK-IPOP/open-data-pipeline},
  version = {0.2.1},
  year = {2022}
}
```

Thank you.

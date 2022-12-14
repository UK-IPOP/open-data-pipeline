# Medical Examiner Open Data Pipeline

This repository contains the code for the Medical Examiner Open Data Pipeline.

We currently fetch data from the following sources:

- [Cook County Medical Examiner's Archives](https://datacatalog.cookcountyil.gov/Public-Safety/Medical-Examiner-Case-Archive/cjeq-bs86)
- [San Diego Medical Examiner's Office](https://data.sandiegocounty.gov/Safety/Medical-Examiner-Cases/jkvb-n4p7)
- [Milwaukee County Medical Examiner's Office](https://county.milwaukee.gov/EN/Medical-Examiner)

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
benefits of using the CLI via a docker image is that you don't have to have Python3.10 or the drug toolbox on your local machine 🙂.

We utilize async methods to speed up the large number of web requests we make to the data sources.

> It is important to regularly fetch/pull from this repo to maintain an updated `config.json`

We currently do not guarantee Windows support unfortunately. If you want to help make that a reality, please submit a new [Pull Request](https://github.com/UK-IPOP/open-data-pipeline/pulls)

There is further API-documentation available on the GitHub Pages [website](https://uk-ipop.github.io/open-data-pipeline/) for this repo if you want to interact with the CLI.
I would recommend using the docker image as it is easier to use and always referring to the CLI `--help` for more information.

### Workflow

The workflow can best be described by looking at the `pipeline.yml` file.

![Workflow](./imgs/workflow.png)

## Requirements

- Python 3.10
- Drug Extraction ToolBox

## Installation

To install the python cli I recommend using [pipx](https://pypa.github.io/pipx/).

```bash
pipx install opendata-pipeline
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

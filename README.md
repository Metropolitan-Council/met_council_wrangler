# Met Council Network Wrangler

> **NOTE:** This repository is currently under development and is not yet in a fully functional state. Please check back for future updates.

## Overview

Met Council Wrangler is Python package developed to assist Met Council network creation and management. Council network approach use these open source packages:

- **[Ranch](https://github.com/wsp-sag/ranch):** Create travel model-ready networks from OpenStreetMap and GTFS feeds.
- **[Network Wrangler](https://github.com/wsp-sag/network_wrangler):** Network and scenario management. Define edits via Project Cards.
- **[Project Card](https://github.com/network-wrangler/projectcard):** Define project card standard, schema, validation.
- **[Cube Wrangler](https://github.com/network-wrangler/cube_wrangler):** Convert Network Wrangler networks to/from Cube format.
- **Met Council Wrangler (this repo):** Council-specific parameters and variables, centroid connector integration, other network utilities.
- **[Project Card Registry](https://github.com/Metropolitan-Council/project_card_registry):** Web database reconcile new node numbering conflicts across concurrent project coding.

## Structure

Repo contain Python package `met_council_wrangler` with Council-specific roadway and transit parameters and methods:

- `met_council_wrangler/metcouncil_parameters.py`: Parameters (projection, county lookups, etc.) specific to Council model.
- `met_council_wrangler/metcouncil_roadway.py`: Roadway network variable creation methods.
- `met_council_wrangler/metcouncil_transit.py`: Transit network variable creation methods.
- `metcouncil_data/`: Reference data (area type, count, county, lookups, TAZ, etc.) used building Council networks.
- `examples/`: Example Cube and GTFS-based inputs demonstrate workflows.
- `notebooks/`: Notebooks illustrate project card creation and version workflows.
- `tests/`: Unit tests.

## Prerequisites

Before use, have these installed:

- **Operating System:** Windows: Some components of the model rely on Cube Voyager, which is only supported on Windows.
- **Python environment manager:** Miniconda (recommended) or Anaconda
- **Cube Voyager 6.5.1:** Required for network skimming and assignment processes. A valid Cube license must be obtained separately.
- **Git:** Required to clone repo


Additional dependencies listed in [requirements.txt](requirements.txt) and [requirements.docs.txt](requirements.docs.txt).

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Metropolitan-Council/met_council_wrangler.git
cd met_council_wrangler
```

### 2. Create the Python Environment

```bash
conda config --add channels conda-forge
conda create python=3.10 rtree geopandas osmnx -n met_council_wrangler
conda activate met_council_wrangler
```

### 3. Install the Package

```bash
pip install -e .
```

Installing Met Council Wrangler also install Network Wrangler, Project Card, Cube Wrangler, and other dependency packages.

## Typical Usage

Flowcharts and notebooks in [docs/index.md](docs/index.md) illustrate typical use cases:

1. Network Creation
2. Creating a Cube Network
3. Creating a Project Card from a Cube Log File
4. Creating a Project Card from Two Cube LIN Files

## More Information

Contact Dennis Farmer (dennis.farmer@metc.state.mn.us) at the Metropolitan Council for questions regarding the overall model.

Cube Voyager can be purchased from [Bentley](https://www.bentley.com/en/products/product-line/mobility-simulation-and-analytics/cube-voyager)

More information about ActivitySim can be found at the [ActivitySim Website](https://activitysim.github.io/).

<img role="img" aria-label="Metropolitan Council logo" src="main-logo.png" alt="Metropolitan Council logo" style="max-width: 50%; display: block; margin: 0 auto; box-sizing: content-box;background-color: transparent;">
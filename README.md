# Met Council Network Wrangler

> **NOTE:** This repository is currently under development and is not yet in a fully functional state. Please check back for future updates.

## Overview

Met Council Wrangler is a Python package developed to assist with Met Council network creation and management. The Council's network approach uses the following open-source packages:

- **[Ranch](https://github.com/wsp-sag/ranch):** Creates travel model-ready networks from OpenStreetMap and GTFS feeds.
- **[Network Wrangler](https://github.com/wsp-sag/network_wrangler):** Provides network and scenario management and defines edits through Project Cards.
- **[Project Card](https://github.com/network-wrangler/projectcard):** Defines the project card standard, schema, and validation.
- **[Cube Wrangler](https://github.com/network-wrangler/cube_wrangler):** Converts Network Wrangler networks to and from Cube format.
- **Met Council Wrangler (this repository):** Council-specific parameters and variables, centroid connector integration, and other network utilities.
- **[Project Card Registry](https://github.com/Metropolitan-Council/project_card_registry):** Provides a web database for reconciling new node-numbering conflicts across concurrent project coding.

## Structure

The repository contains the Python package `met_council_wrangler`, with Council-specific roadway and transit parameters and methods:

- `met_council_wrangler/metcouncil_parameters.py`: Parameters (projection, county lookups, etc.) specific to the Council model.
- `met_council_wrangler/metcouncil_roadway.py`: Methods for creating roadway network variables.
- `met_council_wrangler/metcouncil_transit.py`: Methods for creating transit network variables.
- `metcouncil_data/`: Reference data (area types, counts, counties, lookups, TAZs, etc.) used to build Council networks.
- `examples/`: Example Cube and GTFS-based inputs that demonstrate workflows.
- `notebooks/`: Notebooks that illustrate project card creation and version workflows.
- `tests/`: Unit tests.

## Typical Usage

Flowcharts and notebooks in [docs/index.md](docs/index.md) illustrate the following typical use cases:

1. Network Creation
2. Creating a Cube Network
3. Creating a Project Card from a Cube Log File
4. Creating a Project Card from Two Cube LIN Files

## More Information

Contact Dennis Farmer (dennis.farmer@metc.state.mn.us) at the Metropolitan Council for questions regarding the overall model.

Cube Voyager can be purchased from [Bentley](https://www.bentley.com/en/products/product-line/mobility-simulation-and-analytics/cube-voyager).

More information about ActivitySim can be found on the [ActivitySim website](https://activitysim.github.io/).

<img role="img" aria-label="Metropolitan Council logo" src="main-logo.png" alt="Metropolitan Council logo" style="max-width: 50%; display: block; margin: 0 auto; box-sizing: content-box;background-color: transparent;">
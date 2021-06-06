# Spanish telephony market evolution

## Overview

This tool purpose is to analyze the historical evolution of the landline and mobile telephony market in Spain.

[Live example can be found here](https://www.serfer2.com/spanish-telephony-market/).

Data source is Spanish Regulatory Entity called [_CNMC_](https://www.cnmc.es/) (Comision Nacional de los Mercados y la Competencia).

Backend data preprocessing routines has been built with Python 3.8. See requirements.txt for more details.

Network graph has been built with [Vis.js](https://visjs.org/), a great JS library for dynamic, browser based visualizations.


## Installation and data generation

### Installation

Clone repositrory and install python dependencies:

```
cd /var/opt
git clone https://github.com/serfer2/spanish-telephony-market.git
cd spanish-telephony-market/
pip install -r requirements.txt
```

Run tests for checking:

```
python -m unittest
```

### Data generation

Generate data:

```
python -m backend.preprocess_data
```

## Deployment

The following example shows how to deploy user interface components to be served with an HTTP server like Nginx:

```
cp -R /var/opt/spanish-telephony-market/ui/* <your_http_server_root_directory>/spanish-telephony-market
chown -R www-data:www-data <your_http_server_root_directory>/spanish-telephony-market/*
service nginx restart
```

## License

Licensed under [GNU General Public License (GPLv3)](https://www.gnu.org/licenses/gpl-3.0.html).

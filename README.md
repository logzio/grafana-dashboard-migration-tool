# Grafana dashboard migration tool
A simple tool to migrate your grafana dashboards to Logz.io platform with minimal effort. Based on Python 3.7

### Dependencies:
|  | version |
|---|---|
|requests|2.25.0|
|regex|2020.11.13|
|Grafana|6 or higher|

### How to use:
* Clone the repo:
``` bash
git clone https://github.com/logzio/grafana-dashboard-migration-tool.git
```
* Switch directory to the repo:
```bash
cd grafana-dashboard-migration-tool
```
* Run the script, you will be asked to configure your enviroment variables:
```bash
python main.py # If python 3 is your default version
```
```bash
python3 main.py # If python 2 is your default version
```

### Configuration:
| Enviroment variable | Description |
|---|---|
| GRAFANA_HOST | Your grafana host without protocol specification (e.g. localhost:3000). |
| GRAFANA_TOKEN | Your grafana editor/admin API key, find or create one under Configuration -> API keys. |
| LOGZIO_API_TOKEN | Your Logz.io account API token, find it under settings -> tools -> manage tokens -> API tokens. |
| REGION_CODE | Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further information. |

### Limitations
* Grfana dashboards with schema version 14 or lower that containes "rows" objects will not be uploaded, you will receive a warning log. Please consider to update your dashboards schema version to the latest.

* The`p8s_logzio_name` variable will not added to panels queries that doesn't contines filtering, you will receive a warning log.
* Some panel types are not supported by Logz.io platform. If your dahboard containes unsupported panel type you will receive a warning log, and you may have some issues while rendering the panel in logz.io.

* Dashboards that include annotations, notification endpoints, and other external resources are imported without these resources during bulk import.

* Custom selection of dashboards is not possible with bulk import. All your dashboard folders are imported to a single folder within Logz.io.

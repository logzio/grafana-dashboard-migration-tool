# Grafana dashboard migration tool
A simple tool to migrate your grafana dashboards to Logz.io platform with minimal effort. Based on Python 3.8

### How to use

- Clone the repo:
``` bash
git clone https://github.com/logzio/grafana-dashboard-migration-tool.git
```
- Switch directory to the repo:
```bash
cd grafana-dashboard-migration-tool
```
- Install poetry, and install dependencies

```bash
pip install poetry
poetry install
```

- Run the script, you will be asked to configure your enviroment variables, or you can export them :
```bash
GRAFANA_TOKEN="XXXXXXXXXXXXXXXXX" \
GRAFANA_PROTO="http" \
GRAFANA_HOST="grafana.example.com" \
REGION_CODE="us" \
LOGZIO_API_TOKEN="XXXXXXXXXXXXXXXXX" \
poetry run python main.py
```
- In your logz.io metrics account check your `Uploaded by script` folder to see all dashboards
### Configuration:
| Enviroment variable | Description |
|---|---|
| GRAFANA_HOST | Your grafana host without protocol specification (e.g. localhost:3000). |
| GRAFANA_TOKEN | Your grafana editor/admin API key, find or create one under Configuration -> API keys. |
| LOGZIO_API_TOKEN | Your Logz.io account API token, find it under settings -> manage tokens -> API tokens. |
| GRAFANA_PROTO | Protocol to access your grafana instance. Defaults to `https`. |
| REGION_CODE | Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further information. |

### Limitations
- Grafana dashboards with schema version 14 or lower that contains "rows" objects will not be uploaded, you will receive a warning log. Please consider updating your dashboards schema version to the latest.

- Dashboards that include annotations, notification endpoints, and other external resources are imported without these resources during bulk import.

- Custom selection of dashboards is not possible with bulk import. All your dashboard folders are imported to a single folder within Logz.io.

### Contributors
* Romain Guilmont [@rguilmont](https://github.com/rguilmont)

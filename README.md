# Grfana dashboard migration tool
A simple tool to migrate your grafana dashboards to Logz.io platform with minimal effort. Based on Python 3.7

### Dependencies:
| Libarary | version |
|---|---|
|requests|2.25.0|
|regex|2020.11.13|

### How to use:
* Clone the repo:
``` bash
git clone https://github.com/logzio/grafana-dashboard-migration-tool.git
```
* Switch directory to the repo:
```bash
cd grafana-dashboard-migration-tool
```
* Set your enviroment varaiables in `configuration.py`
* Run the script with your configuration:
```bash
python main.py 
```

### Configuration:
| Enviroment variable | Description |
|---|---|
| GRAFANA_HOST | Your grafana host without protocol specification (e.g. localhost:3000). |
| GRAFANA_TOKEN | Your grafana editor/admin API key, find or create one under Configuration -> API keys. |
| LOGZIO_API_TOKEN | Your Logz.io account API token, find it under settings -> tools -> manage tokens -> API tokens. |
| REGION_CODE | Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further information. |
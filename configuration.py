import os

os.environ['GRAFANA_HOST'] = '' # Your grafana host without protocol specification (e.g. localhost:3000).
os.environ['GRAFANA_TOKEN'] = '' # Your grafana editor/admin API key, find or create one under Configuration -> API keys.
os.environ['LOGZIO_API_TOKEN'] = '' # Your Logz.io account API token, find it under settings -> tools -> manage tokens -> API tokens.
os.environ['REGION_CODE'] = '' # Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further information.

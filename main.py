import os
import logging
logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)
logging.getLogger().setLevel(logging.INFO)
logging.info('Installing dependencies')
os.system('pip install -r requirements.txt')
import json
import requests
import input_validator


GRAFANA_HOST = input('Enter your GRAFANA_HOST:')
GRAFANA_TOKEN = input('Enter your GRAFANA_TOKEN:')
LOGZIO_API_TOKEN = input('Enter your LOGZIO_API_TOKEN:')
REGION_CODE = input('Enter your REGION_CODE:')

REQUEST_HEADERS = {
    'Authorization': 'Bearer {}'.format(GRAFANA_TOKEN),
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'User-Agent': None
}

LOGZIO_API_HEADERS = {
    'X-API-TOKEN': LOGZIO_API_TOKEN,
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    'User-Agent': None
}

ALERTS = []

SUPPORTED_PANELS = ['graph', 'grafana-worldmap-panel', 'grafana-piechart-panel', 'singlestat', 'dashlist',
                    'alertlist', 'text', 'heatmap', 'bargauge', 'table', 'gauge', 'stat', 'row']

# validate inputs
input_validator.is_valid_grafana_host(GRAFANA_HOST)
input_validator.is_valid_grafana_api_token(GRAFANA_TOKEN)
input_validator.is_valid_logzio_api(LOGZIO_API_TOKEN)
BASE_API_URL = input_validator.is_valid_region_code(REGION_CODE)

BASE_URL = 'http://{}/api'.format(GRAFANA_HOST)
UPLOAD_DASHBOARD_URL = '{}dashboards/db'.format(BASE_API_URL)
ALL_DASHBOARDS_URL = '{}/search'.format(BASE_URL)


# set dashboard values before upload and creating new dashboard with grafana api
def _init_parameters(dashboard, fid):
    try:
        dashboard['overwrite'] = True
        dashboard['folderId'] = fid
        dashboard['dashboard']['id'] = None
        dashboard['dashboard']['editable'] = True
        dashboard['dashboard']['uid'] = None
        dashboard['dashboard']['refresh'] = "30s"
    except KeyError as e:
        logging.error(
            'At `{}` dashboard, error occurred while setting dashboard parameters'.format(dashboard['dashboard'],
                                                                                          ['title']))


# Get all dashboards as json from grafana host
def _init_dashboard_list(uid_list, base_url, r_headers):
    dashboards_list = []
    for uid in uid_list:
        request_url = '{}/dashboards/uid/{}'.format(base_url, uid)
        response = requests.get(request_url, headers=r_headers)
        dashboard = response.json()
        try:
            del dashboard['meta']
        except KeyError:
            logging.error('At {}')
        dashboards_list.append(dashboard)
    return dashboards_list


# Creates new folder for uploaded dashboards, if the folder already exists, the dashboards in the folder wil be overwriten
def _create_uploaded_folder():
    folder_url = '{}folders'.format(BASE_API_URL)
    folder_id = None
    new_title = 'Uploaded by script'
    folders_list = json.loads(requests.get(folder_url, params={}, headers=LOGZIO_API_HEADERS).text)
    for folder in folders_list:
        if folder['title'] == new_title:
            folder_id = folder['id']
            logging.info('Found existing `Uploaded by script` folder with id: {}'.format(str(folder_id)))
    if not folder_id:
        folder_data = {
            "uid": None,
            "title": new_title
        }
        new_folder = requests.post(url=folder_url, json=folder_data, params={}, headers=LOGZIO_API_HEADERS).json()
        folder_id = new_folder['id']
        logging.info('New folder created with id: {}'.format(str(folder_id)))

    return folder_id


# Adding panel types to dedicated list
def _get_panel_types(panels, panel_types):
    for panel in panels:
        try:
            panel_types.append(panel['type'])
        except Exception as e:
            logging.error(e)


# check for unsupported panel types
def _inspect_panels_types(dashboard):
    panel_types = []
    _get_panel_types(dashboard['dashboard']['panels'], panel_types)
    panel_types = list(dict.fromkeys(panel_types))
    for t in panel_types:
        if t not in SUPPORTED_PANELS:
            alert = "`{}` dashboard: `{}` panel type is not supported and can cause issues when rendering the dashboard".format(
                dashboard['dashboard']['title'], t)
            ALERTS.append(alert)


def _update_panels_datesources(dashboard, ds_name, var_list):
    try:
        var_list.append(
            {'name': 'p8s_logzio_name', 'datasource': '$datasource', 'type': 'query', 'query': 'label_values('
                                                                                          'p8s_logzio_name)'})
        for panel in dashboard['dashboard']['panels']:
            panel['datasource'] = '${}'.format(ds_name)
            _add_enviroment_label(panel, dashboard['dashboard']['title'])
    except KeyError as e:
        logging.error('KeyError: {}'.format(e))


# Recursive function to generate query with the `p8s_logzio_name` label
def _generate_query(query_string, env_filter_string):
    if '{' not in query_string:
        return query_string
    idx = query_string.index('{') + 1
    new_query = query_string[:idx] + env_filter_string
    query_string = query_string[idx:]
    return new_query + _generate_query(query_string, env_filter_string)

# Adding `p8s_logzio_name` label to all query strings in the dashboard
def _add_enviroment_label(panel, title):
    env_filter_string = 'p8s_logzio_name="$p8s_logzio_name",'
    try:
        q_idx = 0
        if not panel['type'] == 'row' and not panel['type'] == 'text':
            for query in panel['targets']:
                query_string = query['expr']
                if '{' in query_string:
                    new_query = _generate_query(query_string, env_filter_string)
                    panel['targets'][q_idx]['expr'] = new_query
                    q_idx += 1
                else:
                    ALERTS.append(
                        'At `{}` dashboard: failed to add `p8s_logzio_name` to filtering in panel: {}'.format(title, panel[
                            'title']))
    except KeyError as e:
        logging.error('at _add_enviroment_label: {}'.format(e))

# Checking panels for Static datasource reference, will create dynamic datasource variable if not exists
def _validate_templating(dashboard):
    try:
        var_list = dashboard['dashboard']['templating']['list']
        has_ds = False
        for var in var_list:
            if var['type'] == 'datasource' and var['query'] == 'prometheus':
                has_ds = True
                datasource_name = var['name']
        if not has_ds:
            new_ds = {
                'name': 'datasource',
                'type': 'datasource',
                'query': 'prometheus'
            }
            datasource_name = new_ds['name']
            var_list.append(new_ds)

        dashboard['dashboard']['templating']['list'] = var_list
        _update_panels_datesources(dashboard, datasource_name, var_list)
    except KeyError as e:
        logging.info('At `{}` dashboard - an error has occurred while editing the dashboard: {}'.format(
            dashboard['dashboard']['title'], e))


# main script
def main():
    all_dashboards = requests.get(ALL_DASHBOARDS_URL, headers=REQUEST_HEADERS).json()
    uids = []
    for item in all_dashboards:
        try:
            uids.append(item['uid'])
        except TypeError as e:
            raise TypeError(all_dashboards['message'])
    # init list
    dashboards_list = _init_dashboard_list(uids, BASE_URL, REQUEST_HEADERS)
    # create new folder to store the dashboards
    folder_id = _create_uploaded_folder()

    for dashboard in dashboards_list:
        if "rows" not in dashboard['dashboard'].keys() or dashboard['dashboard']['schemaVersion'] > 14:
            _init_parameters(dashboard, folder_id)
            _validate_templating(dashboard)
            _inspect_panels_types(dashboard)
            try:
                upload_response = requests.post(url=UPLOAD_DASHBOARD_URL, data=json.dumps(dashboard), params={},
                                                headers=LOGZIO_API_HEADERS)
            except Exception as e:
                logging.error("At `{}` dashboard - upload error : {}".format(dashboard['dashboard']['title'], e))
            if upload_response.status_code == 200:
                logging.info("`{}` dashboard uploaded successfully, schema version: {}, status code: {}".format(
                    dashboard['dashboard']['title'], dashboard['dashboard']['schemaVersion'],
                    upload_response.status_code))
            else:
                logging.error(
                    'At `{}` dashboard - upload error: {} - schema version: {}'.format(dashboard['dashboard']['title'],
                                                                                       upload_response.text,
                                                                                       dashboard['dashboard'][
                                                                                           'schemaVersion']))
        else:
            ALERTS.append(
                'At `{}` dashboard: cannot parse "rows" object, please consider to update the dashboard schema '
                'version, current version: {}'.format(dashboard['dashboard']['title'], dashboard[
                    'dashboard']['schemaVersion']))
    for alert in sorted(ALERTS):
        logging.warning(alert)


if __name__ == "__main__":
    main()

import json
import logging
import os
from functools import reduce
from typing import Dict

import coloredlogs
import requests

import input_validator
import prometheus

ALERTS = []
SUPPORTED_PANELS = ['graph', 'grafana-worldmap-panel', 'grafana-piechart-panel', 'singlestat', 'dashlist',
                        'alertlist', 'text', 'heatmap', 'bargauge', 'table', 'gauge', 'stat', 'row', 'timeseries', 'logs']

logger = logging.getLogger(__name__)
coloredlogs.install(level='INFO')

# read variable either from environment or, if not found, from input.
def _read_variable(name: str) -> str:
    if name in os.environ:
        val = os.environ[name]
        logger.info("Took from environment {}".format(val))
        return val
    return input("Enter your {}:".format(name))


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
        logger.error(
            'At `{}` dashboard, error occurred while setting dashboard parameters'.format(dashboard['dashboard'],
                                                                                          ['title']))


# Get all dashboards as json from grafana host
def _init_dashboard_list(uid_list, base_url, r_headers):
    dashboards_list = []
    for uid in uid_list:
        request_url = f'{base_url}dashboards/uid/{uid}'
        response = requests.get(request_url, headers=r_headers)
        dashboard = response.json()
        try:
            del dashboard['meta']
        except KeyError:
            pass
        dashboards_list.append(dashboard)
    return dashboards_list


# Creates new folder for uploaded dashboards, if the folder already exists, the dashboards in the folder wil be
# overwriten
def _create_uploaded_folder(logzio_url: str, logz_api_headers: Dict[str, str]):
    folder_url = '{}folders'.format(logzio_url)
    folder_id = None
    new_title = 'Uploaded by script'
    resp = requests.get(folder_url, params={}, headers=logz_api_headers)
    resp.raise_for_status()
    
    for folder in resp.json():
        if folder['title'] == new_title:
            folder_id = folder['id']
            logger.info('Found existing `Uploaded by script` folder with id: {}'.format(str(folder_id)))
    if not folder_id:
        folder_data = {
            "uid": None,
            "title": new_title
        }
        new_folder = requests.post(url=folder_url, json=folder_data, params={}, headers=logz_api_headers).json()
        folder_id = new_folder['id']
        logger.info('New folder created with id: {}'.format(str(folder_id)))

    return folder_id


# Adding panel types to dedicated list
def _get_panel_types(panels, panel_types):
    for panel in panels:
        try:
            panel_types.append(panel['type'])
        except Exception as e:
            logger.error(e)


# check for unsupported panel types
def _inspect_panels_types(dashboard):
    panel_types = []
    _get_panel_types(dashboard['dashboard']['panels'], panel_types)
    panel_types = list(dict.fromkeys(panel_types))
    for t in panel_types:
        if t not in SUPPORTED_PANELS:
            alert = f"`{t}` panel type is not supported, at `{dashboard['dashboard']['title']}` dashboard: you may " \
                    f"experience some issues when rendering the dashboard "
            ALERTS.append(alert)


def _is_prometheus_panel(targets):
    for target in targets:
        if 'expr' not in target.keys():
            return False
    return True


def _update_panels_datesources(dashboard, ds_name, var_list):
    try:
        var_list.append(
            {'name': 'p8s_logzio_name', 'datasource': '$datasource', 'type': 'query', 'query': 'label_values('
                                                                                               'p8s_logzio_name)'})
        for panel in dashboard['dashboard']['panels']:
            if 'alert' not in panel.keys():
                panel['datasource'] = '${}'.format(ds_name)
                if _is_prometheus_panel(panel['targets']):
                    _add_enviroment_label(panel)
            else:
                panel['datasource'] = None
    except KeyError as e:
        pass


def _clear_notifications(dashboard):
    for panel in dashboard['dashboard']['panels']:
        try:
            panel['alert']['notifications'] = []
        except KeyError:
            pass


# Adding `p8s_logzio_name` label to all query strings in the dashboard
def _add_enviroment_label(panel):
    env_filter_string = 'p8s_logzio_name="$p8s_logzio_name",'
    try:
        if panel['type'] not in ['row', 'text']:
            new_label = prometheus.LabelFiltering('p8s_logzio_name', '$p8s_logzio_name')
            def transform_query(acc, target):
                target['expr'] = prometheus.add_filter(target['expr'], new_label)
                acc.append(target)
                return acc
            panel['targets'] = reduce(transform_query, panel['targets'], [])
    except KeyError as e:
        logger.error('at _add_enviroment_label: {}'.format(e))


def _update_query_variables(var_list, datasource_name):
    for var in var_list:
        if var['type'] == 'query':
            var['datasource'] = '${}'.format(datasource_name)
    return var_list


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
        var_list = _update_query_variables(var_list, datasource_name)
        dashboard['dashboard']['templating']['list'] = var_list
        _update_panels_datesources(dashboard, datasource_name, var_list)
    except KeyError as e:
        logger.info('At `{}` dashboard - an error has occurred while editing the dashboard: {}'.format(
            dashboard['dashboard']['title'], e))


# main script
def main():
    logger.info('Configure your environment variables')
    logger.info('Your grafana host without protocol specification (e.g. localhost:3000). ')
    GRAFANA_HOST = _read_variable('GRAFANA_HOST')
    logger.info('Your grafana editor/admin API key, find or create one under Configuration -> API keys.')
    GRAFANA_TOKEN = _read_variable('GRAFANA_TOKEN')
    logger.info('Your Logz.io account API token, find it under settings -> tools -> manage tokens -> API tokens.')
    LOGZIO_API_TOKEN = _read_variable('LOGZIO_API_TOKEN')
    logger.info('Your Logz.io region code. For example if your region is US, then your region code is `us`. You can find your '
        'region code here: https://docs.logz.io/user-guide/accounts/account-region.html#regions-and-urls for further '
        'information.')
    REGION_CODE = _read_variable('REGION_CODE')

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


    # validate inputs
    input_validator.is_valid_grafana_host(GRAFANA_HOST)
    input_validator.is_valid_grafana_api_token(GRAFANA_TOKEN)
    input_validator.is_valid_logzio_api(LOGZIO_API_TOKEN)
    BASE_API_URL = input_validator.is_valid_region_code(REGION_CODE)

    PROTO =  os.environ['GRAFANA_PROTO'] if 'GRAFANA_PROTO' in os.environ else 'https' 
    BASE_URL = '{}://{}/api/'.format(PROTO, GRAFANA_HOST)
    UPLOAD_DASHBOARD_URL = '{}dashboards/db'.format(BASE_API_URL)
    ALL_DASHBOARDS_URL = '{}search'.format(BASE_URL)


    all_dashboards = requests.get(ALL_DASHBOARDS_URL, headers=REQUEST_HEADERS).json()
    uids = []
    for item in all_dashboards:
        try:
            if item['type'] == 'dash-db':
                uids.append(item['uid'])
        except TypeError as e:
            raise TypeError(all_dashboards['message'])
    # init list
    dashboards_list = _init_dashboard_list(uids, BASE_URL, REQUEST_HEADERS)
    # create new folder to store the dashboards
    folder_id = _create_uploaded_folder(BASE_API_URL, LOGZIO_API_HEADERS)

    for dashboard in dashboards_list:
        logger.info(f"Processing dashboard {dashboard['dashboard']['title']}")
        if "rows" not in dashboard['dashboard'].keys() or dashboard['dashboard']['schemaVersion'] > 14:
            _init_parameters(dashboard, folder_id)
            _validate_templating(dashboard)
            _inspect_panels_types(dashboard)
            _clear_notifications(dashboard)
            try:
                
                upload_response = requests.post(url=UPLOAD_DASHBOARD_URL, data=json.dumps(dashboard), params={},
                                                headers=LOGZIO_API_HEADERS)
            except Exception as e:
                logger.error("At `{}` dashboard - upload error : {}".format(dashboard['dashboard']['title'], e))
            if upload_response.ok:
                logger.info("`{}` dashboard uploaded successfully, schema version: {}, status code: {}".format(
                    dashboard['dashboard']['title'], dashboard['dashboard']['schemaVersion'],
                    upload_response.status_code))
            else:
                logger.error(
                    'At `{}` dashboard - upload error: {} - schema version: {}'.format(dashboard['dashboard']['title'],
                                                                                       upload_response.text,
                                                                                       dashboard['dashboard'][
                                                                                           'schemaVersion']))
        else:
            ALERTS.append(
                'cannot parse "rows" object, At `{}` dashboard: please consider to update the dashboard schema '
                'version ️, current version: {}'.format(dashboard['dashboard']['title'], dashboard[
                    'dashboard']['schemaVersion']))
    for alert in sorted(ALERTS):
        logger.warning(alert)


if __name__ == "__main__":
    main()

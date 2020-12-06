"""
This module is for validating user's input
"""

import re


def is_valid_grafana_host(url):
    if type(url) is not str:
        raise TypeError("GRAFANA_HOST should be a string")
    regex = '^(([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])\.)*([a-z0-9]|[a-z0-9][a-z0-9\-]*[a-z0-9])(:[0-9]+)?$'
    match_obj = re.search(regex, url)
    if match_obj is not None and match_obj.group() is not None:
        return True
    raise ValueError("GRAFANA_HOST is invalid: {}".format(url))


def is_valid_logzio_api(url):
    if type(url) is not str:
        raise TypeError("API token should be a string")
    regex = '^[a-z 0-9]+-[a-z 0-9]+-[a-z 0-9]+-[a-z 0-9]+-[a-z 0-9]+$'
    match_obj = re.search(regex, url)
    if match_obj is not None and match_obj.group() is not None:
        return True
    raise ValueError("API token is invalid: {}".format(url))


def is_valid_grafana_api_token(url):
    if type(url) is not str:
        raise TypeError("API token should be a string")
    return True


def is_valid_region_code(code):
    if type(code) is not str:
        raise TypeError("API token should be a string")
    supported_regions = ['us', 'eu', 'uk', 'nl', 'ca', 'au', 'wa']
    if code not in supported_regions:
        raise ValueError('region code is not supported: {}'.format(code))
    if code == 'us':
        return 'https://api.logz.io/v1/grafana/api/'
    else:
        return 'https://api-{}.logz.io/v1/grafana/api/'.format(code)
    return True

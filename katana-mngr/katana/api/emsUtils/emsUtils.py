from katana.api.mongoUtils import mongoUtils
import requests
import json


def conf_radio(emsd):
    """
    Configure radio components for the newly created slice
    """
    ems_list = list(mongoUtils.index('ems'))
    ems_url = ems_list[0]['url']  # Assuming that we have one wim registered
    api_prefix = '/deploy'
    url = ems_url + api_prefix
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    data = emsd
    r = None
    try:
        r = requests.post(url, json=json.loads(json.dumps(data)), timeout=10,
                          headers=headers)
        r.raise_for_status()
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print("Error:", err)

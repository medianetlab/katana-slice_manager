import requests
import json


class Wim():
    """
    Class implementing the communication API with WIM
    """

    def __init__(self, url):
        """
        Initialize an object of the class
        """
        self.url = url

    def register_vim(self, vim):
        """
        Register the added vim to the wim
        """
        wim_url = self.url
        api_prefix = '/api/addvim'
        url = wim_url + api_prefix
        data = vim
        r = None
        try:
            r = requests.post(url, json=json.loads(json.dumps(data)),
                              timeout=10)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("Error:", err)

    def create_slice(self, wsd):
        """
        Create the transport network slice
        """
        wim_url = self.url
        api_prefix = '/api/sm'
        url = wim_url + api_prefix
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        data = wsd
        r = None
        try:
            r = requests.post(url, headers=headers,
                              json=json.loads(json.dumps(data)), timeout=10)
            r.raise_for_status()
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("Error:", err)

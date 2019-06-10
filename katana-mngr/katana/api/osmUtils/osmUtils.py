import requests
import json
from katana.api.mongoUtils import mongoUtils


def select_OSM(id=None):
    """
    Selects a registered OSM instance from the DB and returns it
    """
    if id is None:
        # Assume that there is only one OSM registered
        nfvo_list = list(mongoUtils.index('nfvo'))
        nfvo = nfvo_list[0]
        return nfvo


class Osm():
    """
    Class implementing the communication API with OSM
    """

    def __init__(self, ip, username, password, project_id="admin", timeout=5):
        """
        Initialize an object of the class
        """
        self.ip = ip
        self.username = username
        self.password = password
        self.project_id = project_id
        self.token = ""
        self.timeout = timeout

    def get_token(self):
        """
        Returns a valid Token for OSM
        """
        headers = {
            'Content-Type': 'application/yaml',
            'Accept': 'application/json',
        }

        data = "{username: '" + self.username + "', password: '" + \
            self.password + "', project_id: '" + self.project_id + "'}"
        url = f"https://{self.ip}:9999/osm/admin/v1/tokens"
        response = requests.post(url,
                                 headers=headers, data=data,
                                 verify=False, timeout=self.timeout)
        self.token = response.json()['id']
        # return token id
        return(self.token)

    def addVim(self, vimName, vimPassword, vimType, vimUrl, vimUser, secGroup):
        """
        Registers a VIM to the OSM VIM account list
        Returns VIM id
        """
        osm_url = f"https://{self.ip}:9999/osm/admin/v1/vim_accounts"
        config = {
            "security_groups": secGroup
        }
        data = '{{ name: "{0}", vim_password: "{1}", vim_tenant_name: "{2}",\
            vim_type: "{3}", vim_url: "{4}", vim_user: "{5}" , config: {6}}}'.format(
            vimName, vimPassword, vimName, vimType, vimUrl, vimUser, config)
        while True:
            headers = {
                'Content-Type': 'application/yaml',
                'Accept': 'application/yaml',
                'Authorization': f'Bearer {self.token}',
            }
            response = requests.post(osm_url, headers=headers, data=data, verify=False)
            if (response.status_code != 401):
                vim_id = response.text.split(": ")[1]
                break
            else:
                self.get_token()
        return vim_id

    def instantiate_ns(self, nsName, nsdId, vimAccountId):
        """
        Instantiates a NS on the OSM
        Returns the NS ID
        """
        osm_url = f"https://{self.ip}:9999/osm/nslcm/v1/ns_instances_content"

        data = "{{ nsName: {0}, nsdId: {1}, vimAccountId: {2} }}".format(
            nsName, nsdId, vimAccountId)
        while True:
            headers = {
                'Content-Type': 'application/yaml',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}',
            }
            response = requests.post(osm_url, headers=headers, data=data, verify=False)
            if (response.status_code != 401):
                nsId = response.json()
                break
            else:
                self.get_token()
        return (nsId['id'])

    def get_nsr(self, nsId):
        """
        Returns the NSR for a given NS ID
        """
        osm_url = f"https://{self.ip}:9999/osm/nslcm/v1/ns_instances/{nsId}"
        # Get the NSR from NS ID in json format
        while True:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}',
            }
            response = requests.get(osm_url, headers=headers, verify=False)
            if (response.status_code != 401):
                nsr = response.json()
                break
            else:
                self.get_token()
        return (nsr)

    def get_vnfrId(self, nsr):
        """
        Retrieve list of VNFrIDS from NSR
        """
        vnfrId_list = nsr['constituent-vnfr-ref']
        return (vnfrId_list)

    def get_vnfr(self, vnfrId):
        """
        Retrieve VNFR from VNFRID
        """
        osm_url = f"https://{self.ip}:9999/osm/nslcm/v1/vnf_instances/{vnfrId}"
        # Get the VNFR from VNF ID in json format
        while True:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'Authorization': f'Bearer {self.token}',
            }
            response = requests.get(osm_url, headers=headers, verify=False)
            if (response.status_code != 401):
                vnfr = response.json()
                break
            else:
                self.get_token()
        return (vnfr)

    def get_IPs(self, vnfr):
        """
        Retrieve a list of IPs from a VNFR
        """
        ips = []
        for i in vnfr['vdur']:
            for ip in i['interfaces']:
                ips.append(ip['ip-address'])
        return (ips)

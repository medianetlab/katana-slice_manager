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


def get_token(ip, username, password, project_id='admin', timeout=5):
    """
    Returns a valid Token for OSM
    """
    headers = {
        'Content-Type': 'application/yaml',
        'Accept': 'application/json',
    }

    data = "{username: '" + username + "', password: '" + \
        password + "', project_id: '" + project_id + "'}"
    url = f"https://{ip}:9999/osm/admin/v1/tokens"
    # https://ip_adress:9999/osm/admin/v1/tokens
    response = requests.post(url,
                             headers=headers, data=data,
                             verify=False, timeout=timeout)
    token = response.json()
    # return token
    return(token['id'])


class osmAPI():
    """
    Class implementing the communication API with OSM
    """

    def __init__(self, ip, token, username, password, project_id="admin", timeout=5):
        """
        Initialize an object of the class
        """
        self.ip = ip
        self.osm_username = username
        self.osm_password = password
        self.token = token

    def addVim(self, vimName, vimPassword, vimType, vimUrl, vimUser):
        """
        Registers a VIM to the OSM VIM account list
        Returns VIM id
        """
        osm_url = f"https://{self.ip}:9999/osm/admin/v1/vim_accounts"
        headers = {
            'Content-Type': 'application/yaml',
            'Accept': 'application/yaml',
            'Authorization': f'Bearer {self.token}',
        }
        data = '{{ name: "{0}", vim_password: "{1}", vim_tenant_name: "{2}", vim_type: "{3}", vim_url: "{4}", vim_user: "{5}" }}'.format(
            vimName, vimPassword, vimName, vimType, vimUrl, vimUser)
        response = requests.post(osm_url, headers=headers, data=data, verify=False)
        vim_id = response.text.split(": ")[1]
        return vim_id

    def instantiate_ns(self, nsName, nsdId, vimAccountId):
        """
        Instantiates a NS on the OSM
        Returns the NS ID
        """
        osm_url = f"https://{self.ip}:9999/osm/nslcm/v1/ns_instances_content"
        headers = {
            'Content-Type': 'application/yaml',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }

        data = "{{ nsName: {0}, nsdId: {1}, vimAccountId: {2} }}".format(
            nsName, nsdId, vimAccountId)
        response = requests.post(osm_url, headers=headers, data=data, verify=False)
        nsId = response.json()
        return (nsId['id'])

    def get_nsr(self, nsId):
        """
        Returns the NSR for a given NS ID
        """
        osm_url = f"https://{self.ip}:9999/osm/nslcm/v1/ns_instances/{nsId}"
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }
        # Get the NSR from NS ID in json format
        response = requests.get(osm_url, headers=headers, verify=False)
        nsr = response.json()
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
        headers = {
            'Content-Type': 'application/yaml',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.token}',
        }
        # Get the NSR from NS ID in json format
        response = requests.get(osm_url, headers=headers, verify=False)
        vnfr = response.json()
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

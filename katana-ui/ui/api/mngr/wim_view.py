from flask import Flask, jsonify, request, Response
from flask_classful import FlaskView
import requests
from flask_jwt_extended import jwt_required
from ui.api.mngr import MngrFlaskView




class WimView(MngrFlaskView):

    trailing_slash = False

    @jwt_required
    def index(self):
        return proxy_request_to_katana_mngr(request)

    @jwt_required
    def get(self, id):
        return proxy_request_to_katana_mngr(request)

    @jwt_required
    def delete(self, uuid):
        return proxy_request_to_katana_mngr(request)

    @jwt_required
    def put(self, uuid):
        return proxy_request_to_katana_mngr(request)

    @jwt_required
    def post(self):
        return proxy_request_to_katana_mngr(request)



"""
Until commit df65c9c0ec5ae7930d5145bd9eac947da1f269c4
the code below was inside each function (index / get / delete / put / post)
To reduce repetition of code, we introduce the "proxy_request_to_katana_mngr()" function below.

code from: https://stackoverflow.com/questions/6656363/proxying-to-another-web-service-with-flask
"""
def proxy_request_to_katana_mngr(request):
    resp = requests.request(
        method=request.method,
        url=request.url.replace(request.host_url, 'http://katana-mngr:8000/').replace('/mngr/api','/api'),
        headers={key: value for (key, value) in request.headers if key != 'Host'},
        data=request.get_data(),
        cookies=request.cookies,
        allow_redirects=False)

    excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    headers = [(name, value) for (name, value) in resp.raw.headers.items()
               if name.lower() not in excluded_headers]

    response = Response(resp.content, resp.status_code, headers)
    return response
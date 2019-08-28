from flask import Flask, jsonify, request, Response
from flask_classful import route
import requests

from ui.api.mngr import MngrFlaskView

from flask_jwt_extended import (
    jwt_optional,
    jwt_required,
    get_jwt_identity,
    current_user
)



class ApiView(MngrFlaskView):

    # code from: https://stackoverflow.com/questions/6656363/proxying-to-another-web-service-with-flask

    @route('/vim')
    @route('/vim/<id>', endpoint='vim_handle')
    @jwt_required
    def vim_handle(self, id):

        resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'http://katana-mngr:8000/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response

    # @app.route('/post/<int:post_id>')
    # @route('/vim/<uuid:uuid_value>')
    # @jwt_required
    # def vim_handle_with_uuid(uuid_value):

    #     resp = requests.request(
    #         method=request.method,
    #         url=request.url.replace(request.host_url, 'http://katana-mngr:8000/'),
    #         headers={key: value for (key, value) in request.headers if key != 'Host'},
    #         data=request.get_data(),
    #         cookies=request.cookies,
    #         allow_redirects=False)

    #     excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
    #     headers = [(name, value) for (name, value) in resp.raw.headers.items()
    #                if name.lower() not in excluded_headers]

    #     response = Response(resp.content, resp.status_code, headers)
    #     return response



    @route('/wim/<id>', endpoint='wim_handle')
    @jwt_required
    def wim_handle(self, id):

        resp = requests.request(
            method=request.method,
            url=request.url.replace(request.host_url, 'http://katana-mngr:8000/'),
            headers={key: value for (key, value) in request.headers if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False)

        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for (name, value) in resp.raw.headers.items()
                   if name.lower() not in excluded_headers]

        response = Response(resp.content, resp.status_code, headers)
        return response

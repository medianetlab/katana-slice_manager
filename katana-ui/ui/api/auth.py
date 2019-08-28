from flask import jsonify, request
from flask_classful import FlaskView
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    set_access_cookies,
    unset_jwt_cookies
)

from ui.blueprints.user.models import User
from ui.blueprints.user.schemas import auth_schema


class AuthView(FlaskView):
    route_prefix = '/api/'

    def post(self):
        json_data = request.get_json()

        if not json_data:
            response = {
                'error': 'Invalid input'
            }

            return jsonify(response), 400

        
        try:
            data = auth_schema.load(json_data)
        except marshmallow.exceptions.ValidationError as err:
            
            print("marshmallow error:", err)

            response = {
                'error': err
            }

            return jsonify(response), 422

        user = User.find_by_identity(data['identity'])

        if user and user.authenticated(password=data['password']):
            access_token = create_access_token(identity=user.username)

            response = jsonify({
                'data': {
                    'access_token': access_token
                }
            })

            # Set the JWTs and the CSRF double submit protection cookies.
            set_access_cookies(response, access_token)

            return response, 200

        response = jsonify({
            'error': {
                'message': 'Invalid identity or password'
            }
        })

        return response, 401

    @jwt_required
    def delete(self):
        response = jsonify({
            'data': {
                'logout': True
            }
        })

        # Because the JWTs are stored in an httponly cookie now, we cannot
        # log the user out by simply deleting the cookie in the frontend.
        # We need the backend to send us a response to delete the cookies
        # in order to logout. unset_jwt_cookies is a helper function to
        # do just that.
        unset_jwt_cookies(response)

        return response, 200

from flask import jsonify, request

from ui.api.v1 import V1FlaskView
from ui.blueprints.user.models import User
from ui.blueprints.user.schemas import registration_schema


class UserView(V1FlaskView):
    def post(self):
        json_data = request.get_json()
        print(json_data)

        if not json_data:
            response = jsonify({'error': 'Invalid input'})

            return response, 400

        try:
          data = registration_schema.load(json_data)
        except marshmallow.exceptions.ValidationError as err:
            
            print("marshmallow error:", err)
            response = {
                'error': err
            }

            return jsonify(response), 422


        user = User()
        user.email = data.get('email')
        user.username = data.get('username')
        user.password = User.encrypt_password(data.get('password'))
        user.save()

        return jsonify(data), 200

from flask_classful import FlaskView


class V1FlaskView(FlaskView):
    route_prefix = '/api/v1/'

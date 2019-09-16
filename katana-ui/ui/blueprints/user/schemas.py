from marshmallow import fields, validate, ValidationError

from ui.extensions import marshmallow
from ui.blueprints.user.models import User


def ensure_unique_identity(data):
    user = User.find_by_identity(data)

    if user:
        raise ValidationError('{0} already exists'.format(data))

    return data


class RegistrationSchema(marshmallow.Schema):
    email = fields.Email(required=True, validate=ensure_unique_identity)
    username = fields.Str(required=True,
                          validate=[validate.Length(min=3, max=255),
                                    ensure_unique_identity])
    password = fields.Str(required=True,
                          validate=validate.Length(min=8, max=128))


class AuthSchema(marshmallow.Schema):
    identity = fields.Str(required=True,
                          validate=validate.Length(min=3, max=255))
    password = fields.Str(required=True,
                          validate=validate.Length(min=8, max=128))


registration_schema = RegistrationSchema()
auth_schema = AuthSchema()

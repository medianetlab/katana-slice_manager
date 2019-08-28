import click
import random

from datetime import datetime

from faker import Faker

from ui.app import create_app
from ui.extensions import db
from ui.blueprints.user.models import User

# Create an app context for the database connection.
app = create_app()
db.app = app

fake = Faker()


def _log_status(count, model_label):
    """
    Log the output of how many records were created.

    :param count: Amount created
    :type count: int
    :param model_label: Name of the model
    :type model_label: str
    :return: None
    """
    click.echo('Created {0} {1}'.format(count, model_label))

    return None


def _bulk_insert(model, data, label):
    """
    Bulk insert data to a specific model and log it. This is much more
    efficient than adding 1 row at a time in a loop.

    :param model: Model being affected
    :type model: SQLAlchemy
    :param data: Data to be saved
    :type data: list
    :param label: Label for the output
    :type label: str
    :param skip_delete: Optionally delete previous records
    :type skip_delete: bool
    :return: None
    """
    with app.app_context():
        model.query.delete()

        db.session.commit()
        db.engine.execute(model.__table__.insert(), data)

        _log_status(model.query.count(), label)

    return None


@click.group()
def cli():
    """ Add items to the database. """
    pass


@click.command()
def users():
    """
    Generate fake users.
    """
    random_emails = []
    data = []

    click.echo('Working...')

    # Ensure we get about 20 unique random emails.
    for i in range(0, 19):
        random_emails.append(fake.email())

    random_emails.append(app.config['SEED_USER_EMAIL'])
    random_emails = list(set(random_emails))

    while True:
        if len(random_emails) == 0:
            break

        created_on = fake.date_time_between(
            start_date='-1y', end_date='now').strftime('%s')
        created_on = datetime.utcfromtimestamp(
            float(created_on)).strftime('%Y-%m-%dT%H:%M:%S Z')

        email = random_emails.pop()

        random_trail = str(int(round((random.random() * 1000))))
        username = fake.first_name() + random_trail

        params = {
            'created_on': created_on,
            'updated_on': created_on,
            'email': email,
            'username': username.lower(),
            'password': User.encrypt_password('password')
        }

        # Ensure the seeded user has the seeded config settings.
        if email == app.config['SEED_USER_EMAIL']:
            params['username'] = app.config['SEED_USER_USERNAME']
            password = User.encrypt_password(app.config['SEED_USER_PASSWORD'])
            params['password'] = password

        data.append(params)

    return _bulk_insert(User, data, 'users')


@click.command()
@click.pass_context
def all(ctx):
    """
    Generate all data.

    :param ctx:
    :return: None
    """
    ctx.invoke(users)

    return None


cli.add_command(users)
cli.add_command(all)

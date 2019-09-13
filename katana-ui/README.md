# katana-ui

Flask application to provide a UI for `katana-mngr`.


## Where to start...
 - how this container starts can be found at the `docker-compose.yaml` file at the root folder of the repo.
 - how this container is built can be found at the [Dockerfile](./Dockerfile)
 - which flask-plugins and python libraries are used can be found at the [requirements.txt](./requirements.txt)


## Gunicorn
 - to modify things like listening port, logs, hot-reload... go to the `docker-compose.yaml` file, `katana-ui` service and modify:

        command: gunicorn -b 0.0.0.0:8080 --access-logfile - --reload "ui.app:create_app()"


## Database / cli tool for initialization
- this app needs a database (for users/passwords etc). In the `docker-compose.yaml` file it's the service with name `postgres`
- to initialize the database use the cli tool `ui`:
    1. get "inside" the container with `docker container exec -it katana-ui bash`
    2. `ui db init`
    3. `ui db seed`

> ⚠️ **Warning**: Not using `init` and `seed` after the first time you run the app makes it crash!

## Database Configuration
 - can be modified at the [.env](./.env) file:
 
       POSTGRES_USER=mnladmin
       POSTGRES_PASSWORD=devpassword
       POSTGRES_DB=mnladmin


## UI admin user/pass
- can be modified at the [config/settings.py](./config/settings.py) file:

       SEED_USER_EMAIL = 'admin@local.host'
       SEED_USER_USERNAME = 'admin'
       SEED_USER_PASSWORD = 'password'

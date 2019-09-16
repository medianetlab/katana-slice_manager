# katana-ui

Flask application to provide a UI for `katana-mngr`.


**Where to start...**
 - how this container starts can be found at the `docker-compose.yaml` file at the root folder of the repo.
 - how this container is built can be found at the [Dockerfile](./Dockerfile)
 - which flask-plugins and python libraries are used can be found at the [requirements.txt](./requirements.txt)


**Gunicorn**
 - to modify things like listening port, logs, hot-reload... go to the `docker-compose.yaml` file, `katana-ui` service and modify:

        command: gunicorn -b 0.0.0.0:8080 --access-logfile - --reload "ui.app:create_app()"

**UI admin user/pass**
- can be modified at the [config/settings.py](./config/settings.py) file:

       SEED_USER_EMAIL = 'admin@local.host'
       SEED_USER_USERNAME = 'admin'
       SEED_USER_PASSWORD = 'password'

<br>
<br>
<br>



## Database

### Initialization
- this app needs a database (for users/passwords etc). In the `docker-compose.yaml` file it's the service with name `postgres`
- to initialize the database use the cli tool `ui`:
    1. get "inside" the container with `docker container exec -it katana-ui bash`
    2. `ui db init`
    3. `ui db seed`

> ⚠️ **Warning**: Not using `init` and `seed` after the first time you run the app makes it crash!

### Configuration
 - can be modified at the [.env](./.env) file:
 
       POSTGRES_USER=mnladmin
       POSTGRES_PASSWORD=devpassword
       POSTGRES_DB=mnladmin

### Deletion
- data are stored to a named docker `volume`. This means that even if you `docker-compose up` / `docker-compose down`, the data will be there.
- in case that you need a fresh start, first `docker-compose down` and then find and delete the relative `volume`. Depending on your folder names/configuration, it will be something like:

        docker volume rm katanaslicemanager_postgres


<br>
<br>
<br>




## Page routes & templates
Page routes can be found inside the [/ui/blueprints/](./ui/blueprints/) folder:
- page-related routes: [/ui/blueprints/page/views.py](./ui/blueprints/page/views.py)
- user-related page routes: [/ui/blueprints/user/views.py](./ui/blueprints/user/views.py)

The folder structure looks similar to this:

    .
    ├── page
    │   ├── templates
    │   │   └── page
    │   │       ├── ems.html
    │   │       ├── home2.html
    │   │       ├── home.html
    │   │       ├── nfvo.html
    │   │       ├── vim.html
    │   │       └── wim.html
    │   └── views.py
    └── user
        ├── templates
        │   └── user
        │       ├── login.html
        │       └── signup.html
        └── views.py

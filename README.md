# Vespa-Watch

Django app for the monitoring and management of [_Vespa velutina_](https://www.inaturalist.org/taxa/119019-Vespa-velutina), an invasive species in Belgium.

## Installation (local development)

_Note: deployment instructions of application are provided in [deployment dir](https://github.com/inbo/vespa-watch/blob/master/deployment/setup.md)_

### Setup database

1. Create an empty PostgreSQL database (e.g. `vespa-watch`)
2. Enable PostGIS: `CREATE EXTENSION postgis;`

### Define settings

1. Clone this repository: `git clone https://github.com/inbo/vespa-watch`
2. Copy [`djangoproject/settings/settings_local.template.py`](djangoproject/settings/settings_local.template.py) to `djangoproject/settings/settings_local.py`
3. In that file, verify the database settings are correct and set `SECRET_KEY` to a non-empty value

### Setup Python environment

1. Create a virtual environment, e.g. `conda create -n vespawatch python=3.6`
2. Activate the environment, e.g. `source activate vespawatch`
3. Navigate to the project directory and install the requirements: `pip install -r requirements.txt`
4. Tell Django to use the local settings: `export DJANGO_SETTINGS_MODULE=djangoproject.settings.settings_local`

### Node package manager

Make sure you have npm installed. You'll need to run an npm script to build
all static files.

### Apply database migrations

```bash
python manage.py migrate
```

### Create superuser

* In development (this will prompt for a username, email and password):

    ```bash
    python manage.py createsuperuser
    ```

* In production:

    ```
    python manage.py create_su
    ```

### Load data from iNaturalist

Initialize the database with observations from iNaturalist (optional):

```bash
python manage.py sync_pull
```

### Generate static files

The repository contains a number of raw static files that need to be processed
before deployment. You can build all static files with an npm script:

```bash
$ npm install # first time only
$ npm run build:all
```

### Run the application

In your virtual environment:

```bash
$ export DJANGO_SETTINGS_MODULE=djangoproject.settings.settings_local
$ python manage.py runserver
```

Go to http://localhost:8000 to see the application.

## Development tips

### Update HTML

HTML is defined in [templates](https://docs.djangoproject.com/en/2.1/topics/templates/) at [`vespawatch/templates/vespawatch`](vespawatch/templates/vespawatch). `base.html` is the main template, almost all other templates build upon it. The HTML is structured around [Bootstrap v4.0](https://getbootstrap.com/docs/4.0/getting-started/introduction/) classes for layout, components and utilities: use these before writing custom html and css.

### Node package manager (npm) for static files

**Important**: static files in the Django accessible directory [`vespawatch/static/vespawatch`](vespawatch/static/vespawatch) should not be edited manually: those are all generated! They are managed in [`assets`](assets) and copied or compiled with Node Package Manager using `npm run build:all`. To start:

1. Verify [npm](https://www.npmjs.com/get-npm) is installed: `node -v`
2. Go to the root of this repository
2. Install all dependencies with: `npm install` (will read [`package.json`](package.json) to create the `node_modules` directory)

### Update CSS

CSS is managed as SCSS, starting from Bootstrap's SCSS, with custom variable overwrites in `_variables.scss` and custom CSS in `main.scss`. These get bundled together with Bootstrap in a single `vespawatch/static/vespawatch/css/main.css`.

1. Go to [`assets/scss`](assets/scss)
2. Update the relevant `.scss` files
3. Generate the CSS automatically on every change with `npm run watch:css` (or once with `npm run create:css`).

### Update libraries

External Javascript libraries (and their CSS) are defined in [`package.json`](package.json). To add a library:

1. Add the library and version in [`package.json`](package.json) under `dependencies` 
2. Install the library with `npm install`
3. Create a new script in `package.json` under `scripts` to move the necessary JS & CSS files to `vespawatch/static/vespawatch/libraries` (see the other scripts for inspiration) and add your script to `copy:libraries`
4. Move the files with `npm run copy:libraries`
5. Link to the files in your template with:
    ```html
    <link rel="stylesheet" href="{% static 'vespawatch/libraries/my_library/my_library.min.css' %}">
    <script src="{% static 'vespawatch/libraries/my_library/my_library.min.js' %}"></script>
    ```
    
### Update Javascript

1. Go to [`assets/js`](assets/js)
2. Update the relevant `.js` files
3. Copy the files automatically on every change with `npm run watch:js` (or once with `npm run copy:custom-js`)

### Update images

1. Go to [`assets/img`](assets/img)
2. Add or update the relevant image files
3. Copy the files with `npm run copy:img`

### Translations

1. Extract the translations from the code to .po files

   ```bash
   $ python manage.py makemessages -l nl -l fr
   $ python manage.py makemessages -d djangojs -l nl -l fr
   ```
2. Complete the translations in `locale/*/LC_MESSAGES/django.po` and `locale/*/LC_MESSAGES/djangojs.po`. A simple text editor is enough, but more advanced tools such as Qt Linguist can more convenient.

3. Compile .po => .mo
    ```bash
    $ python manage.py compilemessages
    ```
4. Rince and repeat.    

## Contributors

[List of contributors](https://github.com/inbo/vespa-watch/contributors)

## License

[MIT License](https://github.com/inbo/vespa-watch/blob/master/LICENSE)

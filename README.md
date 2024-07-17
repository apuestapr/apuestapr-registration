#### Basic Readme for Apuestra Registration

This app runs python flask to provide a web app that handles
user registration.

### Hosting
The application is hosted in three different environment applications on
Render.com

- Dev
- Staging
- Production

### Services
The following are services that support the application.

- Whitehat Gaming - KYC verification processes.
- Auth0 - Identity Management
- Mongo Atlas - Basic Data Storage.
- Onfido - ???

### Auth Providers
Auth0 provides username and password login only. (TBD)

### Setting Up Environment
Use this to install poetry for dependency management.
```curl -sSL https://install.python-poetry.org | python3.11 -```

### Setting a Dev Environment
Use this to create a Python environment.
```python3 -m venv env```

Use this to activate the `venv` for the project.
```source env/bin/activate```

Use this to install the dependencies
```pip install -r requirements.txt```

Use this to check what dependencies are installed.
```poetry show```

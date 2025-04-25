# Apuestapr Registration App Troubleshooting Guide

This document outlines common issues and solutions when setting up and running the Apuestapr Registration application locally.

## Setting Up the Environment

### Virtual Environment Setup

The application uses Poetry for dependency management. To activate the Poetry-created virtual environment:

```bash
source $(poetry env info --path)/bin/activate
```

Or directly use the path:

```bash
source /Users/[username]/Library/Caches/pypoetry/virtualenvs/apuestapr-registration-[hash]-py3.11/bin/activate
```

### Missing Dependencies

If you encounter a `ModuleNotFoundError: No module named 'pkg_resources'` error:

```
ModuleNotFoundError: No module named 'pkg_resources'
```

Install the setuptools package:

```bash
pip install setuptools
```

## Running the Application

Run the Flask application:

```bash
flask run
```

The application will start on http://127.0.0.1:5502.

## Auth0 Configuration

### Callback URL Mismatch Error

If you encounter an error like:

```
Oops!, something went wrong
Callback URL mismatch.
The provided redirect_uri is not in the list of allowed callback URLs.
```

You need to add the callback URLs to your Auth0 application settings:

1. Log in to the [Auth0 Dashboard](https://manage.auth0.com/)
2. Go to Applications > Your Application
3. Add the following URLs to the "Allowed Callback URLs" field:
   ```
   http://127.0.0.1:5502/auth0/callback,
   https://127.0.0.1:5502/auth0/callback,
   http://localhost:5502/auth0/callback,
   https://localhost:5502/auth0/callback
   ```
4. Save the changes

### Alternative Solution

Alternatively, you can modify the .flaskenv file to match the Auth0 configuration:

```
APP_URL=http://127.0.0.1:5502
```

## External Services

The application relies on the following external services:

- MongoDB Atlas for database
- Auth0 for authentication
- Onfido for KYC verification
- Whitehat Gaming for player verification

Ensure all relevant API keys and connection strings in .flaskenv are up to date.

## Common Errors

### MongoDB Connection Issues

If you have trouble connecting to MongoDB, verify:

- The MONGO_CONNECTION_STRING in .flaskenv is correct
- Your IP address is allowlisted in MongoDB Atlas
- Network connectivity to MongoDB Atlas

### Auth0 Login Issues

If login fails after the Auth0 callback URL is fixed:

- Check that AUTH0_CLIENT_ID and AUTH0_CLIENT_SECRET are correct
- Verify the AUTH0_DOMAIN setting
- Ensure proper redirect URLs are configured in Auth0

import functools
import json
import os

import flask

# from authlib.client import OAuth2Session
from authlib.integrations.requests_client import OAuth2Session
import google.oauth2.credentials
import googleapiclient.discovery

import app.google_auth as google_auth

app = flask.Flask(__name__)
# app.secret_key = os.environ.get("FN_FLASK_SECRET_KEY", default=False)
app.secret_key = "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"

app.register_blueprint(google_auth.app)

@app.route('/')
def index():
    if google_auth.is_logged_in():
        user_info = google_auth.get_user_info()
        return '<div>You are currently logged in as ' + user_info['given_name'] + '<div><pre>' + json.dumps(user_info, indent=4) + "</pre>"

    return 'You are not currently logged in.'
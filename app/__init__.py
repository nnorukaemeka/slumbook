from flask import Flask
from flask_pymongo import PyMongo
from flask_restful import Api
import os


MONGO_URI = os.environ.get("MONGO_URI", default=False)

# Initialize application
app = Flask(__name__, static_folder='static', template_folder='templates')

# #Initialize Flask PyMongo
mongo = PyMongo(app,MONGO_URI)

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", default=False)

#initialize RESTful
api = Api(app)

# Import the application
from . import backview, views, google_auth
# from . import google_auth
from flask import Flask
from flask_pymongo import PyMongo
from flask_restful import Api


MONGO_URI = "mongodb+srv://nnorukaemeka:oluchukwu@cluster0.k3hbu.mongodb.net/slumbook1?retryWrites=true&w=majority"

# Initialize application
app = Flask(__name__, static_folder='static', template_folder='templates')

# #Initialize Flask PyMongo
mongo = PyMongo(app,MONGO_URI)

app.config["SECRET_KEY"] = "TooHARDtOkNOW"

#initialize RESTful
api = Api(app)

# Import the application
from . import backview, views, google_auth
# from . import google_auth
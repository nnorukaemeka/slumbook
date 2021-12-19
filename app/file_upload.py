#######################################################################
##################  IMPORTING LIBRARIES   ##############################
from requests.api import get
from app import app, mongo
import os, uuid
from flask import Flask, flash, request, redirect, url_for, send_from_directory, abort
from werkzeug.utils import secure_filename
# from werkzeug.middleware.shared_data import SharedDataMiddleware


#######################################################################
##################  CONFIGURATION   ##############################
# APP_ROOT = os.path.dirname(__file__)
# UPLOAD_FOLDER = os.path.join(app.instance_path, 'UPLOAD_FOLDER')
ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
# ALLOWED_EXTENSIONS = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', xlsx]

# app = Flask(__name__, static_folder='static')
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['ALLOWED_EXTENSIONS'] = ALLOWED_EXTENSIONS
app.config['MAX_IMAGE_FILESIZE'] = 0.5 * 1024 * 1024 #limit the maximum allowed payload to 16 megabytes


#######################################################################
##################  DEFINING FUNCTIONS   ##############################
def allowed_image_filesize(filesize):
    if int(filesize) <= app.config['MAX_IMAGE_FILESIZE']:
        return True
    else:
        return False


def gen_randomname(filename):
    rndstr = str(uuid.uuid4().hex)[:8]  # get a random 8 string in a UUID fromat
    ext = filename.rsplit('.', 1)[1]
    return rndstr+'.'+ext

def allowed_file(filename):
    if not '.' in filename:
        return False
    ext = filename.rsplit('.', 1)[1]
    if ext.lower() in app.config['ALLOWED_EXTENSIONS']:
        return True
    else:
        return False


def uploadfile(file):
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return {"status": False, "message": "Selected file must have a filename"}
    elif not allowed_file(file.filename):
        return {"status": False, "message": "Selected file extension is not allowed"}
    else:
        randomname = gen_randomname(file.filename)
        filename = secure_filename(randomname.lower())
        # file.save(os.path.join(APP_ROOT,filename))
        # file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        mongo.save_file(filename, file)
        return{"status": True, "message": "File sucessfully saved.", "name": filename}

def displayfile(filename):
    try:
        # return send_from_directory(APP_ROOT, filename=filename, as_attachment=False)
        # return mongo.send_file(filename)
        getme = mongo.send_file(filename)
        print("getme  ", getme)
        return getme
    except FileNotFoundError:
        abort(404)

def downloadfile(filename):
    try:
        url = "https://tolemsoft.herokuapp.com/api/user/uploads"
        return send_from_directory(url, filename=filename, as_attachment=False)
    except FileNotFoundError:
        abort(404)
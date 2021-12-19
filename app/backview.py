#################################################
#Import Libraries, Modules
#################################################
from app import app, mongo, api
from flask import render_template, jsonify, request, redirect, url_for, session,logging, flash
from datetime import date, datetime, timedelta
import re, os, smtplib, uuid
from werkzeug.security import generate_password_hash, check_password_hash
from app.sendmail import send_mails
from functools import wraps
from app.file_upload import uploadfile, displayfile
from flask_restful import Resource,reqparse


##################################################
#Functions to call for specific tasks
##################################################
SECRET_KEY = '\x1c\x9e*\x1cO\xa3\xd26\xe9\xf6y\xae/n"\x83\xb2jiA\x9b\xec\xd5\xb0'

#Check if user is logged in
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login','danger')
            return redirect(url_for("signin"))
    return wrap

#Function that returns year.
def footer_year():
    today = date.today()
    year = today.strftime("%Y")
    return (year)

#Nigerian time
def nigerian_time():
    now = datetime.utcnow() + timedelta(hours=1)
    today = date.today()
    d2 = today.strftime("%B %d, %Y")
    tm = now.strftime("%H:%M:%S")
    return (d2 +' '+'at'+' '+tm)

def stamp():
    return str(datetime.utcnow() + timedelta(hours=1))


################################################
#Endpoints or Routes start here
################################################

class SlumbookUsers(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('firstname', 
                        type=str,
                        required=True, 
                        help="Enter First name. Field cannot be left blank")
    parser.add_argument('lastname', 
                        type=str,
                        required=True,
                        help="Enter Last name. Field cannot be left blank")
    parser.add_argument('email', 
                        type=str,
                        required=True,
                        help="Enter Email. Field cannot be left blank")
    parser.add_argument('password', 
                        type=str,
                        required=True,
                        help="Enter Password. Field cannot be left blank")
    parser.add_argument('cpassword', 
                        type=str,
                        required=True,
                        help="Enter Confirm Password. Field cannot be left blank")
    # parser.add_argument('passport', 
    #                     type=str,
    #                     help="Enter Recent Passport. Field cannot be left blank")
    
    def get(self):
        register = mongo.db.signup
        check = register.find({}, {"_id":0}) #list of dict
        results = [item for item in check]
        if not results:
            return {"status":True, "message":"Oops! No result found.", "data":[]}, 200
        else:
            return {"status":True, "message":"result retrieved", "data": results, "count":len(results)}, 200
    
    def post(self):
        data = SlumbookUsers.parser.parse_args()
        _fname = data["firstname"]
        _lname = data["lastname"]
        _email = data["email"]

        #Validation of inputs
        if not (3<=len(_fname)<=50) or not (3<=len(_lname)<=50):
            return {"status":False, "message":"Names must be 3char min and 50char max", "data": ""}, 400
        elif not _email or not re.match(r'[^@]+@[^@]+\.[^@]+', _email):
            return {"status":False, "message":"invalid email address", "data": ""}, 400
        elif not len(data["password"])>3:
            return {"status":False, "message":"Password cannot be less than 4 characters", "data": ""}, 400
        elif not data["password"] == data["cpassword"]:
            return {"status":False, "message":"Password mismatch", "data": ""}, 400
        
        #check database to see if email already exists.
        register = mongo.db.signup
        check = register.find_one({"email":_email})
        if check:
            return {"status":False, "message":"User already exists", "data": ""}, 401

        #all checks are okay, register the new user
        # hash the password
        password_hash = generate_password_hash(data["password"])

        # # compare database password and input password
        # if check_password_hash(password_hash, data['password'])

        #create activation string for Email activation
        activation_string = str(uuid.uuid4().hex)  # get a random string in a UUID fromat
        activation_url = "https://tellbook.herokuapp.com/activateuser/{0}".format(activation_string)
        
        #upload image.
        print("starting image upload")
        if not request.files.get("passport"):
            print("no image file")
            image_name = None
            image_path = None
        else:
            print("getting file")
            _passport = request.files["passport"]
            print(_passport)
            image = uploadfile(_passport)
            if not image["status"]:
                message = image["message"]
                return {"status":False, "message":message, "data": ""}, 400
            else:
                image_name = image["name"]
                image_path = 'https://tellbook.herokuapp.com/api/v1/users/uploads/' + image_name
            
        #POST new user details to slumbook database
        post = {"given_name":_fname, "family_name":_lname, "email":_email, "password":password_hash, "image_name":image_name, "picture":image_path, activation_string:"yes", "activation_string":activation_string, "activation_status":"0", "activation_set_time":stamp(), "signup_channel":"app", "signup_time":stamp()}
        register.insert_one(post)
        print("saved successfully")

        #send SMS
        # mail = send_mail(receiver= _email, subject="ACCOUNT ACTIVATION", body=render_template("sms/accountactivation.txt", name=_fname.upper(), activation_url=activation_url))
        name=_fname.upper()
        msg="Please click on the above button to activate your account."
        mail = send_mails(sender='Tolemsoft Technologies', receiver=_email, subject="Activate Your Account", name=name, token=activation_url, token_name="ACCOUNT ACTIVATION!", message=msg)
        if not mail["status"]:
            print({"status": False, "message": mail["message"]})

        return {"status":True, "message":"Successful! A one-time activation token has been sent to {0}. Activate within 24hours.".format(_email), "data": ""}, 200

api.add_resource(SlumbookUsers, '/api/v1/users')


class SlumbookGmail(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('id', 
                        type=str,
                        required=True, 
                        help="Enter user id. Field cannot be left blank")
    parser.add_argument('email', 
                        type=str,
                        required=True, 
                        help="Enter user email. Field cannot be left blank")
    parser.add_argument('verified_email', 
                        type=str,
                        required=True, 
                        help="Enter verified_email. Field cannot be left blank")
    parser.add_argument('given_name', 
                        type=str,
                        required=True, 
                        help="Enter user given_name. Field cannot be left blank")
    parser.add_argument('family_name', 
                        type=str,
                        required=True, 
                        help="Enter user family_name. Field cannot be left blank")
    parser.add_argument('picture', 
                        type=str,
                        required=True, 
                        help="Enter user picture. Field cannot be left blank")
    parser.add_argument('locale', 
                        type=str,
                        help="Enter user locale. Field cannot be left blank")

    def post(self):
        user_info = SlumbookGmail.parser.parse_args()
        print(user_info)
        #check database to see if email already exists.
        email = user_info["email"]

        register = mongo.db.signup
        check = register.find_one({"email":email})
        if check:
            return {"status":False, "message":"User already exists", "data": ""}, 401
        id = user_info["id"]
        given_name = user_info["given_name"]
        family_name = user_info["family_name"]
        picture = user_info["picture"]
        verified_email = user_info["verified_email"]
        locale = user_info["locale"]
        #POST new user details to slumbook database
        post = {"id": id, "given_name":given_name, "family_name":family_name, "email":email, "picture":picture, "verified_email":verified_email, "locale":locale,"signup_channel":"gmail", "signup_time":stamp()}
        register.insert_one(post)
        print("saved successfully")
        return {"status":True, "message":"User info successfully saved.", "data": ""}, 200
api.add_resource(SlumbookGmail, '/api/v1/users/gmail')


#Change password
class ChangePassword(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('email', 
                        type=str,
                        required=True,
                        help="Enter Email. Field cannot be left blank")
    parser.add_argument('old_password', 
                        type=str,
                        required=True,
                        help="Enter Current Password. Field cannot be left blank")
    parser.add_argument('new_password', 
                        type=str,
                        required=True,
                        help="Enter New Password. Field cannot be left blank")

    def put(self):
        data = ChangePassword.parser.parse_args()
        _email = data["email"]

        #check database to see if email already exists.
        register = mongo.db.signup
        check = register.find_one({"email":_email})
        if not check or check["activation_status"]!="1":
            return {"status":False, "message":"Invalid credentials", "data": ""}, 400
        # Hash password in the database
        password_hash = check["password"]

        # compare database password and input password
        if not check_password_hash(password_hash, data["old_password"]):
            return {"status":False, "message":"Invalid credentials", "data": ""}, 400
        
        # hash the password
        new_password_hash = generate_password_hash(data["new_password"])
        register.update_one({"email":_email}, {'$set': {"password": new_password_hash, "last_update": stamp()}})
        return {"status":True, "message":"Password chnage successfully", "data": ""}, 200

api.add_resource(ChangePassword, '/api/v1/users/changepassword')


#Display pictures
class DisplayFile(Resource):
    def get(self, filename):
        return displayfile(filename)
api.add_resource(DisplayFile, '/api/v1/users/uploads/<string:filename>')
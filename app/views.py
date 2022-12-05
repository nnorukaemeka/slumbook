#################################################
#Import Libraries, Modules
#################################################
from email import message
from time import time
from flask.wrappers import Response
from app import app, mongo
from flask import render_template, jsonify, request, redirect, url_for, session,logging, flash
from datetime import date, datetime, timedelta
import re, os, smtplib, uuid, requests, json
from werkzeug.security import generate_password_hash, check_password_hash
from app.sendmail import send_mails
from functools import wraps
from app.file_upload import uploadfile, displayfile

import app.google_auth as google_auth
# app.register_blueprint(google_auth.app)

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

# config message
# Before execution, turn ON your 'less secure apps' here https://myaccount.google.com/lesssecureapps, and ENABLE https://accounts.google.com/DisplayUnlockCaptcha
def send_mail(receiver, subject, body):
    try:
        gmail_user = "nnorukaemeka@gmail.com"
        gmail_pwd = "ssfjphomvdegivxv"
        sender = gmail_user
        receiver = receiver
        subject = subject
        body = body
        message = """\From: %s\nTo: %s\nSubject: %s\n\n%s""" % ("noreply@slumbook.com.ng", receiver, subject, body)
        smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        smtpserver.ehlo()
        smtpserver.starttls()
        smtpserver.ehlo
        smtpserver.login(gmail_user, gmail_pwd)
        smtpserver.sendmail(sender, receiver, message)
        smtpserver.close()
        return {'status': True, "message": "mail sent succesfully"}

    except Exception as e:
        return {'status': False, "message": e}
        # return {'status': False, "message": "SMTPAuthenticationError: Mail could not be sent."}


################################################
#Endpoints or Routes start here
################################################

#home page
@app.route("/")
def homepage():
    if google_auth.is_logged_in():
        user_info = session["user_info"]
        # #flash a message
        # session["user_info"] = user_info
        # message = "You are currently logged in as {0}".format(user_info['given_name'])
        # flash(message, "success") #success is a category
        return render_template("dashboard.html", title=f"{user_info['given_name']}-Profile | Tolemsoft",year=footer_year())

    return render_template("index.html", title="Home | Tolemsoft", player="player", videoId="cEUJ0EO-ncA", year=footer_year())


#Blog page
@app.route("/blog")
def blog():
    return render_template("blog.html", title="Blog | Tolemsoft",year=footer_year())


#Newsletter
@app.route("/newsletter", methods=["POST"])
def newsletter():
    if request.method == "POST":
        #Get form fields
        _email = request.form['email']

        if not re.match(r'[^@]+@[^@]+\.[^@]+', _email):
            #flash a message
            message = "invalid email address"
            flash(message, "danger") #danger is a category
            return redirect(url_for("homepage"))
            
        _time = nigerian_time()
        
        #post to slumbook database
        post = {"email":_email, "time":_time}
        send = mongo.db.newsletter
        send.insert(post)
        print("saved successfully")

        #flash a message
        message = "Thank you for subscribing to our newsletter."
        flash(message, "success") #success is a category
        return redirect(url_for("homepage"))

#Contact
@app.route("/contact", methods=["POST"])
def contact():
    if request.method == "POST":
        #Get form fields
        _name = request.form['name']
        _email = request.form['email']
        _subject = request.form['subject']
        _message = request.form['message']


        #Validation of inputs
        if not _name or len(_name)<3:
            #flash a message
            message = "Name cannot be less than 3 characters"
            flash(message, "danger") #danger is a category
            return redirect(url_for("homepage"))

        elif not _subject or len(_subject)<5:
            #flash a message
            message = "Subject cannot be less than 5 characters"
            flash(message, "danger") #danger is a category
            return redirect(url_for("homepage"))

        elif not _email or not re.match(r'[^@]+@[^@]+\.[^@]+', _email):
            #flash a message
            message = "invalid email address"
            flash(message, "danger") #danger is a category
            return redirect(url_for("homepage"))

        elif not _message or len(_message)<8:
            #flash a message
            message = "Message cannot be less than 8 characters"
            flash(message, "danger") #danger is a category
            return redirect(url_for("homepage"))
        
        _time = nigerian_time()
        
        #post to slumbook database
        post = {"name":_name, "subject":_subject, "email":_email, "message":_message, "time":_time}
        send = mongo.db.contact
        send.insert(post)
        print("saved successfully")

        #send SMS
        # mail1 = send_mail(receiver= "nnorukaemeka@gmail.com", subject=_subject, body=render_template("sms/admincontact.txt", message=_message, name=_name.upper(), email=_email))
        # mail2 = send_mail(receiver= _email, subject="RE: {}".format(_subject), body=render_template("sms/usercontact.txt", name=_name.upper()))

        name=_name.upper()
        msg=_message +"\n\n\n"+name+"\n"+_email
        mail1 = send_mails(sender='Tolemsoft Technologies', receiver="nnorukaemeka@gmail.com", subject="CONTACT US", name="Admin", token="#", token_name=_subject, message=msg)

        name=_name.upper()
        msg="Thank you for contacting Tolemsoft Technologies. We will get back to you shortly."
        mail2 = send_mails(sender='Tolemsoft Technologies', receiver=_email, subject="RE: {}".format(_subject), name=name, token="#", token_name="Thank you!", message=msg)

        if not mail1["status"]:
            print({"status": False, "message": mail1["message"]})
        elif not mail2["status"]:
            print({"status": False, "message": mail2["message"]})

        #flash a message
        message = "Thank you for contacting us. We will respond to you shortly via {0}".format(_email)
        flash(message, "success") #success is a category
        return redirect(url_for("homepage"))

    # else:
    #     return render_template("contact.html", title="Contact | Tolemsoft",year=footer_year())


#Sign Up page
@app.route("/signup", methods=["GET","POST"])
def signup():
    if request.method == "POST":

        payload = {
            "firstname" : request.form['fname'],
            "lastname" : request.form['lname'],
            "email" : str(request.form['email']).lower(),
            "password" : request.form['password'],
            "cpassword" : request.form['cpassword']
        }
        # Load file (image)
        if request.files["passport"]:
            file = request.files['passport']
            files = {'passport': (file.filename, file.read(), file.content_type)}
        else:
            files = None

        try:
            print("files to be uploaded ", files)
            url = "https://tellbook.herokuapp.com/api/v1/users"
            # r = requests.request(method="POST", url=url, json=payload)
            # response = json.loads(r.content)
            r = requests.post(url=url, data=payload, files=files)
            response = r.json()
            print("response ", response)
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("signup"))


        if response.get("status"):
            message = response["message"]
            flash(message, "success") #success is a category
            return redirect(url_for("signin"))

        else:
            message = response["message"]
            flash(message, "danger") #danger is a category
            return redirect(url_for("signup"))
    else:
        return render_template("signup.html", title="Sign Up | Tolemsoft", player="player", videoId="_fei3yjsD3A", year=footer_year())



#Display pictures
@app.route("/user/uploads/<string:filename>")
def files(filename):
    return displayfile(filename)

#Sign Up page
@app.route("/signin",  methods=["GET", "POST"])
def signin():
    if request.method == "POST":
        #Get form fields
        _email = str(request.form['email']).lower()

        #Validation of inputs
        if not _email or not re.match(r'[^@]+@[^@]+\.[^@]+', _email):
            #flash a message
            message = "Invalid credentials."
            flash(message, "danger") #danger is a category
            return redirect(url_for("signin"))

        #check database to see if email already exists.
        register = mongo.db.signup
        check = register.find_one({"email":_email}, {"_id":0})
        if not check:
            #flash a message
            message = "Invalid credentials."
            flash(message, "danger") #danger is a category
            return redirect(url_for("signin"))
        elif check.get("activation_status") != "1":
            #flash a message
            message = "Account not activated yet."
            flash(message, "danger") #danger is a category
            return redirect(url_for("signin"))

        # Hash password in the database
        password_hash = check["password"]

        # compare database password and input password
        if not check_password_hash(password_hash, request.form['password']):
            message = "Invalid credentials."
            flash(message, "danger") #danger is a category
            return redirect(url_for("signin"))

        # Login the user
        check.pop("password")
        AUTH_TOKEN_KEY = os.environ.get("AUTH_TOKEN_KEY", default=False)
        session.clear()
        session[AUTH_TOKEN_KEY] = True
        session["user_info"] = check
        print(session["user_info"])

        #flash a message
        # message = "You are now logged in"
        message = "You are currently logged in as {0}".format(check['given_name'])
        flash(message, "success") #success is a category
        return redirect(url_for("homepage"))

    else:
        return render_template("signin.html", title="Login | Tolemsoft",player="player", videoId="WNLtjO0o-_A", year=footer_year())

#Dashboard page
@app.route("/dashboard",  methods=["GET", "POST"])
# @login_required
def dashboard():
    return render_template("youtube.html", title=f"Emeka-Profile | Tolemsoft",year=footer_year())
    # return render_template("signin.html", title="{0}Profile | Tolemsoft".format(name),year=footer_year())

#Admin page
@app.route("/admin")
def admin():
    if not google_auth.is_logged_in():
        flash("You must be logged in.", "danger") #danger is a category
        return redirect(url_for("homepage"))
    
    #check database to see if email already exists.
    try:
        url = "https://tellbook.herokuapp.com/api/v1/users"
        r = requests.get(url)
        response = r.json()
    except Exception as e:
        flash(e, "danger") #danger is a category
        return redirect(url_for("homepage"))

    # if response["status"]:
    users = response["data"]
    print(users)
    return render_template("admin.html", title=f"Admin | Tolemsoft", users=users, year=footer_year())
    
    # return render_template("signin.html", title="{0}Profile | Tolemsoft".format(name),year=footer_year())

#Signout page
# @app.route("/signout")
# @login_required
# def signout():
#     session.clear()
#     message = "You are now signed out"
#     flash(message, "dsuccess") #danger is a category
#     return redirect(url_for("signin"))

# #Youtube page
# @app.route("/youtube")
# def youtube():
#     pass
#     return render_template("youtube.html")

#Activation Page
@app.route("/activateuser/<string:token>", methods=["GET", "POST"])
def activateuser(token):
    #check database to see if token exists.
    register = mongo.db.signup
    # check = register.find_one({"activation_string":token}) #searching for value
    check = register.find_one({token: {"$exists": True}}) #searching for key
    if not check:
        #flash a message
        message = "Invalid Token."
        flash(message, "danger") #danger is a category
        return redirect(url_for("signup"))
    elif datetime.strptime(check["activation_set_time"],'%Y-%m-%d %H:%M:%S.%f') < datetime.utcnow() + timedelta(hours=1) - timedelta(hours=24):
        #flash a message
        message = "Token has expired."
        flash(message, "danger") #danger is a category
        return redirect(url_for("signup"))
    elif check["activation_status"]=="1":
        #flash a message
        message = "Account already activated!"
        flash(message, "danger") #danger is a category
        return redirect(url_for("signin"))
    else:
        register.update_one({token: {"$exists": True}}, {"$set": {"activation_status": "1", "activation_time": stamp()}})
        message = "Activation successful! You can now login."
        flash(message, "success") #success is a category
        return redirect(url_for("signin"))



#verify signin page
@app.route("/verifysignin",  methods=["GET"])
def verifysignin():
    return render_template("newenglish.html")



#Vehicle Renewal Registration page
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        print("I'm here")

        payload = {
            "phone_number" : request.form['phone_number'],
            "plate_number" : request.form['plate_number'].upper(),
            "vehicle_type" : str(request.form['vehicle_type']).upper()
        }
        headers = {
                    'content-type': 'application/json',
                    'x-access-token': "frsc@idl-5w731qmFdJ8h+8Xrd9PA!safX"
                }
        print(f"Payload: {payload}")
        try:
            url = "https://safe-payy.herokuapp.com/api/v1/vehiclerenewal/register"
            # r = requests.request(method="POST", url=url, json=payload)
            # response = json.loads(r.content)
            r = requests.post(url=url, json=payload, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("register"))


        if response.get("status"):
            message = response["message"]
            flash(message, "success") #success is a category
            return redirect(url_for("register"))

        else:
            message = response["message"]
            flash(message, "danger") #danger is a category
            return redirect(url_for("register"))
    
    else:
        return render_template("registervehicle.html", title="Register | safetech", player="player", videoId="0yyX7zshpvc", year=footer_year())


def getDuration(numberOfMonths):
    month = int(numberOfMonths)
    get_year = month//12
    get_month = month%12
    if month==1:
        duration = f"{month} month"
    elif get_year == 0 and get_month !=0:
        duration = f"{month} months"
    elif get_year==1 and get_month==0:
        duration = f"{get_year} year"
    elif get_year>1 and get_month==0:
        duration = f"{get_year} years"
    elif get_year==1 and get_month!=0:
        new_month = month-(12*get_year)
        if new_month == 1:
            duration = f"{get_year} year and {new_month} month"
        else:
            duration = f"{get_year} year and {new_month} months"
    elif get_year>1 and get_month!=0:
        new_month = month-(12*get_year)
        if new_month == 1:
            duration = f"{get_year} years and {new_month} month"
        else:
            duration = f"{get_year} years and {new_month} months"
    else:
        duration = "Invalid number of months"
    return [month,duration]


#Generate PYMTREF for PLASCHEMA
@app.route("/payref", methods=["GET","POST"])
def payref():
    if request.method == "POST":
        print(request.form)
        
        enrolment_id = request.form.get('enrolment_id')  
        if enrolment_id:
            try:
                url = f"https://pshs3.herokuapp.com/verify/enrid/{enrolment_id}"
                red= requests.post(url=url)
                rese = red.json()
                print(f"enrolment_validation_response: {rese}")
                if not rese.get("status"):
                    message = rese["message"]
                    flash(message, "danger") #danger is a category
                    return redirect(url_for("payref"))
                else:
                    name= rese["data"]["name"].title()
                    enrolment_id = enrolment_id
                    payment_type = "PLASCHEMA Topup"
            except Exception as e:
                message = str(e)
                flash(message, "danger") #danger is a category
                return redirect(url_for("payref"))
        else:
            name = ""
            enrolment_id = ""
            payment_type = "PLASCHEMA form"
        phone_number = request.form['phone_number']
        dura = request.form['duration']
        getduration = getDuration(dura)
        duration = int(getduration[0])
        duration_name = getduration[1]
        merchant_id = "033"
        amount = 1000*int(duration)
        amount = float(str(format(float(amount),".2f")))
        payload = {'customer_id':enrolment_id, 'duration':duration, 'merchant_id':merchant_id, "amount":amount, 'customer_phone':phone_number,'payment_channel':"USSD", "initiating_phone":phone_number}
        headers = {
                    'content-type': 'application/json',
                    'x-access-token': os.environ.get("FIDELITY_KEY")
                }
        url = "https://safe-payy.herokuapp.com/coralpay/pos/paymentreference/generate"
        try:
            r = requests.post(url=url, json=payload, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("payref"))

        if response.get("status"):
            message= f"From any bank, dial {response['data']} or click the link {response['link']} to pay for your subscription."
            data ={'message':message,"paymentref":response['data'], "link":response['link'], 'amount':amount,'enrolment_id':enrolment_id, "name":name, 'phone_number':phone_number, 'payment_type':payment_type, 'duration':duration_name}
            flash(message, "success") #success is a category
            return render_template("payref_success.html", title="success | safetech",data=data, player="player", videoId="0yyX7zshpvc", year=footer_year())

        else:
            message = response["message"]
            flash(message, "danger") #danger is a category
            return redirect(url_for("payref"))
    
    else:
        return render_template("payref.html", title="PYMTREF | safetech", player="player", videoId="0yyX7zshpvc", year=footer_year())


headers = {
            'content-type': 'application/json',
            'x-access-token': os.environ.get("FIDELITY_KEY")
        }
#Payment via Verge
@app.route("/safepayverge", methods=["GET","POST"])
def safepayverge():
    if request.method == "POST":
        print(request.form)
        
        customer_name = request.form['customer_name']
        customer_email = request.form['customer_email']
        customer_phone = request.form['customer_phone']
        amount = request.form['amount']
        merchant_id = request.form['merchant_id']
        customer_id = request.form['customer_id']
        duration = request.form['duration'] if request.form.get("duration") else ""
        # callback_url = f"https://safetech.herokuapp.com/safepayverge/confirm?auth={customer_phone}"

        payload = {'customer_name':customer_name, 'customer_email':customer_email, 'merchant_id':merchant_id, "customer_id":customer_id, "duration":duration, "amount":amount,'customer_phone':customer_phone}
        
        url = "https://safe-payy.herokuapp.com/api/v1/idlcoralpay/verge/invokepayment"
        try:
            r = requests.post(url=url, json=payload, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("safepayverge"))

        if response.get("status"):
            data = response.get("data")
            pay_page_link = data["PayPageLink"]
            return redirect(pay_page_link)

        else:
            message = response["message"]
            flash(message, "danger") #danger is a category
            return redirect(url_for("safepayverge"))
    
    else:
        url = "https://safe-payy.herokuapp.com/coralpay/pos/user/paymenttype2"
        try:
            r = requests.get(url=url, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("safepayverge"))
        merchants = response.get("data")
        return render_template("testVerge.html", title="SafePAYVerge | safetech", merchants=merchants, player="player", videoId="0yyX7zshpvc", year=footer_year())


#verge payment using PYMTREF
@app.route("/safepayvergepaymentref", methods=["GET","POST"])
def safepayvergepaymentref():
    if request.method == "POST":
        print(request.form)
        
        paymentref = request.form['paymentref']
        payload = {'paymentref':paymentref}
        url = "https://safe-payy.herokuapp.com/api/v1/idlcoralpay/verge/paybypaymentref"
        try:
            r = requests.post(url=url, json=payload, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("safepayvergepaymentref"))

        if response.get("status"):
            data = response.get("data")
            pay_page_link = data["PayPageLink"]
            return redirect(pay_page_link)

        else:
            message = response["message"]
            flash(message, "danger") #danger is a category
            return redirect(url_for("safepayvergepaymentref"))
    
    else:
        return render_template("testVergePaymentref.html", title="SafePAYVergePYMTREF | safetech", player="player", videoId="0yyX7zshpvc", year=footer_year())

headers = {
            'content-type': 'application/json',
            'x-access-token': "fidelity_idl-8Xrd9PAYsafX_e5CfFmq137w5"
        }
#Payment via Klump
@app.route("/safepayklump", methods=["GET","POST"])
def safepayklump():
    if request.method == "POST":
        print(request.form)
        
        customer_name = request.form['customer_name']
        customer_email = request.form['customer_email']
        customer_phone = request.form['customer_phone']
        amount = request.form['amount']
        merchant_id = request.form['merchant_id']
        customer_id = request.form['customer_id']
        duration = request.form['duration'] if request.form.get("duration") else ""
        # callback_url = f"https://safetech.herokuapp.com/safepayverge/confirm?auth={customer_phone}"

        payload = {'customer_name':customer_name, 'customer_email':customer_email, 'merchant_id':merchant_id, "customer_id":customer_id, "duration":duration, "amount":amount,'customer_phone':customer_phone}
        
        url = "https://safe-payy.herokuapp.com/api/v1/idlcoralpay/verge/invokepayment"
        try:
            r = requests.post(url=url, json=payload, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("safepayklump"))

        if response.get("status"):
            return render_template("klump.html", title="SafePAYKlump | safetech", payloads=payload, player="player", videoId="0yyX7zshpvc", year=footer_year())

        else:
            message = response["message"]
            flash(message, "danger") #danger is a category
            return redirect(url_for("safepayklump"))
    
    else:
        url = "https://safe-payy.herokuapp.com/coralpay/pos/user/paymenttype2"
        try:
            r = requests.get(url=url, headers=headers)
            response = r.json()
            print(f"Response: {response}")
        except Exception as e:
            flash(e, "danger") #danger is a category
            return redirect(url_for("safepayklump"))
        merchants = response.get("data")
        return render_template("klump_init.html", title="SafePAYKlump | safetech", merchants=merchants, player="player", videoId="0yyX7zshpvc", year=footer_year())




@app.route("/get_my_ip", methods=["GET","POST"])
def get_my_ip():
    time = nigerian_time()
    header = 'Headers: %s', request.headers
    print("header: ", header)
    data1 = request.get_data()
    data = json.loads(data1.decode('utf-8'))
    print("data: ", data)
    REMOTE_ADDR = request.environ.get('REMOTE_ADDR')
    print("REMOTE_ADDR: ", REMOTE_ADDR)
    HTTP_X_FORWARDED_FOR = request.environ.get('HTTP_X_FORWARDED_FOR')
    print("HTTP_X_FORWARDED_FOR: ", HTTP_X_FORWARDED_FOR)
    post = {"time":time, "data":data, "remote_addr":REMOTE_ADDR, "http_x_forwarded_for":HTTP_X_FORWARDED_FOR}
    response = {"time":time, "message":"request logged in successfully"}
    log = mongo.db.request_logs
    log.insert_one(post)
    return jsonify(response), 200
        

############## TEST INTERBANK TRANSFER ######################
from app import app, api
from flask_restful import Resource, Api, reqparse
import requests, json, hashlib

# LIVE
FIDELITY_HASH_KEY = "5cad9984-c82b-4d33-85d7-20804e4d2b30"
FIDELITY_CLIENT_ID = "IDL@Fid"
FIDELITY_CLIENT_KEY = "67ca8447-15bc-4fea-8112-11ff17a7fa85"
FIDELITY_BASE_URL = "https://196.13.161.29/Transfer"


# #TEST
# FIDELITY_HASH_KEY = "ebac1caa-a997-44c5-9852-8509f3778ba7"
# FIDELITY_CLIENT_ID = "IDL@Fid"
# FIDELITY_CLIENT_KEY = "9c8d3b34-7c2f-46f2-b6a1-9772920e861a"
# FIDELITY_BASE_URL = "https://mtnsimswap.fidelitybank.ng:443/CDL_API"

class FidelityTestFundTransfer(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('TransferAmount', 
                        type=str,
                        required=True, 
                        help="Enter Amount. Field cannot be left blank")
    parser.add_argument('DestinationAccount', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryAccount. Field cannot be left blank")
    parser.add_argument('DestinationBankCode', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryBankCode. Field cannot be left blank")
    parser.add_argument('BeneficiaryName', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryName. Field cannot be left blank")
    parser.add_argument('Narration', 
                        type=str,
                        required=True,
                        help="Enter Narration. Field cannot be left blank")
    parser.add_argument('ReferenceNumber', 
                        type=str,
                        required=True,
                        help="Enter ReferenceNumber. Field cannot be left blank")
   
    def post(self):
        data = FidelityTestFundTransfer.parser.parse_args()
        print("FidelityFundTransfer :", data)
        
        key = FIDELITY_HASH_KEY
        amount = str(format(float(data["TransferAmount"]),".1f"))
        macCipher = data["DestinationAccount"] + amount + key
        # MAC = hashlib.sha512(macCipher.encode('ascii'))
        MAC = hashlib.sha512(macCipher.encode('utf-8')).hexdigest()
        print("MAC: ", MAC.upper())

        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'client-id': FIDELITY_CLIENT_ID,
                'client-key': FIDELITY_CLIENT_KEY
            }
        proxies = {
            "https": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293",
            "http": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293"}
        print(f"headers: {headers}")
        s = requests.Session()
        s.proxies.update(proxies)
        payload = {
                    "DestinationAccount": data["DestinationAccount"],
                    "DestinationBankCode": data["DestinationBankCode"],
                    "TransferAmount": float(data["TransferAmount"]),
                    "Narration": data["Narration"],
                    "BeneficiaryName": data["BeneficiaryName"],
                    "ReferenceNumber": data["ReferenceNumber"],
                    "Hash":MAC.upper()
                    }
        print(f"payload posted: {payload}")
        try:
            r = s.get("http://ip.quotaguard.com/", proxies=proxies)
            ip = r.json()['ip']
            print('Your public IP is:', ip)
            url = f"{FIDELITY_BASE_URL}/FidelityFundsTransfer/InterbankTransfer"
            print(f"url: {url}")
            # s = requests.session()
            # responses2 = s.request(method="GET", url=url2, json=payload,  proxies=proxies, headers=headers)
            # responses2 = s.get("http://safetech.herokuapp.com/get_my_ip",json=payload,  proxies=proxies, headers=headers)
            # results2 = responses2.json()
            # print("log_result: ",results2)
            # # s.close()
            # log = mongo.db.response_logs
            # log.insert_one(results2)
            # print("safetech")
            # requests.urllib3.disable_warnings()
            responses = s.post(url=url, json=payload, proxies=proxies, verify=False, headers=headers)
            # responses = requests.post(url=url,data=payload,  proxies=proxies, headers=headers)
            results = responses.json()
            # results = json.loads(responses.content)
            print(results)
            # log = mongo.db.response_logs
            # log.insert_one(results)
            print("i'm at Fidelity")
        except json.decoder.JSONDecodeError as e:
            return {'status': False, 'message': str(e)}
        except TypeError as e:
            return {'status': False, 'message': str(e)}
        except Exception as e:
            return {'status': False, 'message': str(e), "data":""}
        # return results
        # if results["Result"]["responseCode"]=="00":
        if results.get("Result"):
            result = results.get("Result")
            message = result.get("responseMessage")
            if result["responseCode"] == "00":
                return {"status": True, "message": message, "data":result}, 200
            else:
                return {"status": False, "message": message, "data":result}, 400
        else:
            result = results
            message = result.get("Message")
            return {"status": False, "message": message, "data":result}, 400
        # else:
        #     return {"status": False, "message": results["Result"]["responseMessage"], "data":results}, 200
api.add_resource(FidelityTestFundTransfer, '/api/v1/idlfidelitybank/interbank/fundtransfer/test')



############## TEST INTRABANK TRANSFER ######################
class FidelityTestFundTransferIntra(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('TransferAmount', 
                        type=str,
                        required=True, 
                        help="Enter Amount. Field cannot be left blank")
    parser.add_argument('DestinationAccount', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryAccount. Field cannot be left blank")
    parser.add_argument('DestinationBankCode', 
                        type=str, 
                        help="Enter BeneficiaryBankCode. Field cannot be left blank")
    parser.add_argument('BeneficiaryName', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryName. Field cannot be left blank")
    parser.add_argument('Narration', 
                        type=str,
                        required=True,
                        help="Enter Narration. Field cannot be left blank")
    parser.add_argument('ReferenceNumber', 
                        type=str,
                        required=True,
                        help="Enter ReferenceNumber. Field cannot be left blank")
   
    def post(self):
        data = FidelityTestFundTransferIntra.parser.parse_args()
        print("FidelityFundTransfer :", data)
        
        key = FIDELITY_HASH_KEY
        amount = str(format(float(data["TransferAmount"]),".1f"))
        macCipher = data["DestinationAccount"] + amount + key
        # MAC = hashlib.sha512(macCipher.encode('ascii')).hexdigest()
        MAC = hashlib.sha512(macCipher.encode('utf-8')).hexdigest()
        print("MAC: ", MAC.upper())

        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'client-id': FIDELITY_CLIENT_ID,
                'client-key': FIDELITY_CLIENT_KEY
            }
        proxies = {
            "https": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293",
            "http": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293"}
        print(f"headers: {headers}")
        s = requests.Session()
        s.proxies.update(proxies)
        payload = {
                    "DestinationAccount": data["DestinationAccount"],
                    "TransferAmount": float(data["TransferAmount"]),
                    "Narration": data["Narration"],
                    "BeneficiaryName": data["BeneficiaryName"],
                    "ReferenceNumber": int(data["ReferenceNumber"]),
                    "Hash":MAC.upper()
                    }
        print(f"payload posted: {payload}")
        try:
            r = s.get("http://ip.quotaguard.com/", proxies=proxies)
            ip = r.json()['ip']
            print('Your public IP is:', ip)
            url = f"{FIDELITY_BASE_URL}/FidelityFundsTransfer/IntraTransfer"
            print(f"url: {url}")
            # s = requests.session()
            # responses2 = s.request(method="GET", url=url2, json=payload,  proxies=proxies, headers=headers)
            # responses2 = s.get("http://safetech.herokuapp.com/get_my_ip",json=payload,  proxies=proxies, headers=headers)
            # results2 = responses2.json()
            # print("log_result: ",results2)
            # # s.close()
            # log = mongo.db.response_logs
            # log.insert_one(results2)
            # print("safetech")
            # requests.urllib3.disable_warnings()
            responses = s.post(url=url, json=payload, proxies=proxies, headers=headers)
            # responses = requests.post(url=url,data=payload,  proxies=proxies, headers=headers)
            results = responses.json()
            # results = json.loads(responses.content)
            print(results)
            # log = mongo.db.response_logs
            # log.insert_one(results)
            print("i'm at Fidelity")
        except json.decoder.JSONDecodeError as e:
            return {'status': False, 'message': str(e)}
        except TypeError as e:
            return {'status': False, 'message': str(e)}
        except Exception as e:
            return {'status': False, 'message': str(e), "data":""}, 400
        # return results
        # if results["Result"]["responseCode"]=="00":
        if results.get("Result"):
            result = results.get("Result")
            message = result["responseMessage"]
            if result["responseCode"] == "00":
                return {"status": True, "message": message, "data":result}, 200
            else:
                return {"status": False, "message": message, "data":result}, 400
        else:
            result = results
            message = result["responseMessage"]
            return {"status": False, "message": message, "data":result}, 400
        # else:
        #     return {"status": False, "message": results["Result"]["responseMessage"], "data":results}, 200
api.add_resource(FidelityTestFundTransferIntra, '/api/v1/idlfidelitybank/intrabank/fundtransfer/test')

############## TEST INTERBANK NAME ENQUIRY ######################
class FidelityTestInterBankNameEnquiry(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('DestinationAccount', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryAccount. Field cannot be left blank")
    parser.add_argument('DestinationBankCode', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryBankCode. Field can be left blank")
    
    def post(self):
        data = FidelityTestInterBankNameEnquiry.parser.parse_args()
        print("FidelityTestInterBankNameEnquiry :", data)

        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'client-id': FIDELITY_CLIENT_ID,
                'client-key': FIDELITY_CLIENT_KEY
            }
        print(f"headers: {headers}")
        proxies = {
            "https": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293",
            "http": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293"}
        print(f"headers: {headers}")
        s = requests.Session()
        s.proxies.update(proxies)
        payload = {
                    "DestinationAccount": data["DestinationAccount"],
                    "DestinationBankCode": data["DestinationBankCode"]
                    }
        print(f"payload posted: {payload}")
        try:
            r = s.get("http://ip.quotaguard.com/", proxies=proxies)
            ip = r.json()['ip']
            print('Your public IP is:', ip)
            # url = f"{FIDELITY_BASE_URL}/FidelityFundsTransfer/InterbankNamEnquiry"
            url = "https://196.13.161.29/Transfer/FidelityFundsTransfer/InterbankNamEnquiry"
            print(f"url: {url}")
            responses = s.post(url=url, json=payload, proxies=proxies, verify=False, headers=headers)
            results = responses.json()
            print(results)
        except json.decoder.JSONDecodeError as e:
            return {'status': False, 'message': str(e), "data":""}
        except TypeError as e:
            return {'status': False, 'message': str(e),"data":""}
        except Exception as e:
            return {'status': False, 'message': str(e), "data":""}, responses.status_code
        
        if results.get("responseCode") == "00":
            return {"status": True, "message": "Name enquiry successful", "data":results}, 200
        else:
            return {"status": False, "message": "failed", "data":results}, 400
api.add_resource(FidelityTestInterBankNameEnquiry, '/api/v1/idlfidelitybank/interbank/nameequiry/test')


############## TEST INTRABANK NAME ENQUIRY ######################
class FidelityTestIntraBankNameEnquiry(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('DestinationAccount', 
                        type=str,
                        required=True, 
                        help="Enter BeneficiaryAccount. Field cannot be left blank")
    
    def post(self):
        data = FidelityTestIntraBankNameEnquiry.parser.parse_args()
        print("FidelityTestIntraBankNameEnquiry :", data)

        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'client-id': FIDELITY_CLIENT_ID,
                'client-key': FIDELITY_CLIENT_KEY
            }
        print(f"headers: {headers}")
        proxies = {
            "https": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293",
            "http": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293"}
        print(f"headers: {headers}")
        s = requests.Session()
        s.proxies.update(proxies)
        DestinationAccount =  data["DestinationAccount"]
        try:
            r = s.get("http://ip.quotaguard.com/", proxies=proxies)
            ip = r.json()['ip']
            print('Your public IP is:', ip)
            # url = f"{FIDELITY_BASE_URL}/FidelityFundsTransfer/IntrabankNamEnquiry?AccountNumber={DestinationAccount}"
            url = f"https://196.13.161.29/Transfer/FidelityFundsTransfer/IntraNameEnquiry?AccountNumber={DestinationAccount}"
            print(f"url: {url}")
            responses = s.get(url=url, proxies=proxies,verify=False, headers=headers)
            results = responses.json()
            # results = json.loads(responses.text)
            print(results)
        except json.decoder.JSONDecodeError as e:
            return {'status': False, 'message': str(e), "data":""}
        except TypeError as e:
            return {'status': False, 'message': str(e),"data":""}
        except Exception as e:
            return {'status': False, 'message': str(e), "data":""}
        
        if results:
            return {"status": True, "message": "Name enquiry successful", "data":results}, 200
        else:
            return {"status": False, "message": "failed", "data":results}, 400
api.add_resource(FidelityTestIntraBankNameEnquiry, '/api/v1/idlfidelitybank/intrabank/nameequiry/test')


############## TEST INTERBANK REQUERY ######################
class FidelityTestInterBankREQUERY(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('ReferenceNumber', 
                        type=str,
                        required=True,
                        help="Enter ReferenceNumber. Field cannot be left blank")
   
    def post(self):
        data = FidelityTestInterBankREQUERY.parser.parse_args()
        print("FidelityTestInterBankREQUERY :", data)
        
        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'client-id': FIDELITY_CLIENT_ID,
                'client-key': FIDELITY_CLIENT_KEY
            }
        print(f"headers: {headers}")
        s = requests.Session()
        proxies = {
            "https": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293",
            "http": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293"}
        s.proxies.update(proxies)
        params = {
            "ReferenceNumber":data["ReferenceNumber"]
        }
        # ReferenceNumber = data["ReferenceNumber"]
       
        try:
            r = s.get("http://ip.quotaguard.com/", proxies=proxies)
            ip = r.json()['ip']
            print('Your public IP is:', ip)
            url = f"{FIDELITY_BASE_URL}/FidelityFundsTransfer/InterRequery"
            print(f"url: {url}")
            responses = s.get(url=url, proxies=proxies, params=params, verify=False, headers=headers)
            results = responses.json()
            print(results)
        except json.decoder.JSONDecodeError as e:
            return {'status': False, 'message': str(e), "data":""}
        except TypeError as e:
            return {'status': False, 'message': str(e),"data":""}
        except Exception as e:
            return {'status': False, 'message': str(e), "data":""}
        #
        if results.get("Result"):
            result = results.get("Result")
            message = result["responseMessage"]
            if result["responseCode"] == "00":
                return {"status": True, "message": message, "data":result}, 200
            else:
                return {"status": False, "message": message, "data":result}, 400
        else:
            result = results
            message = result["responseMessage"]
            return {"status": False, "message": message, "data":result}, 400
api.add_resource(FidelityTestInterBankREQUERY, '/api/v1/idlfidelitybank/interbank/enquery/test')


############## TEST INTRABANK REQUERY ######################
class FidelityTestIntraBankREQUERY(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('ReferenceNumber', 
                        type=str,
                        required=True,
                        help="Enter ReferenceNumber. Field cannot be left blank")
   
    def post(self):
        data = FidelityTestIntraBankREQUERY.parser.parse_args()
        print("FidelityTestIntraBankREQUERY :", data)
        
        headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json',
                'client-id': FIDELITY_CLIENT_ID,
                'client-key': FIDELITY_CLIENT_KEY
            }
        print(f"headers: {headers}")
        proxies = {
            "https": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293",
            "http": "http://ncxc3t7t5ovtnd:328gqtt234xhhsr6r1a2xjp6p9p@us-east-static-06-a.quotaguard.com:9293"}
        s = requests.Session()
        s.proxies.update(proxies)
        ReferenceNumber = data["ReferenceNumber"]
       
        try:
            r = s.get("http://ip.quotaguard.com/", proxies=proxies)
            ip = r.json()['ip']
            print('Your public IP is:', ip)
            url = f"{FIDELITY_BASE_URL}/FidelityFundsTransfer/IntraRequery?ReferenceNumber={ReferenceNumber}"
            print(f"url: {url}")
            responses = s.get(url=url, proxies=proxies, verify=False, headers=headers)
            results = responses.json()
            print(results)
        except json.decoder.JSONDecodeError as e:
            return {'status': False, 'message': str(e), "data":""}
        except TypeError as e:
            return {'status': False, 'message': str(e),"data":""}
        except Exception as e:
            return {'status': False, 'message': str(e), "data":""}
        #
        if results.get("Result"):
            result = results.get("Result")
            message = result["responseMessage"]
            if result["responseCode"] == "00":
                return {"status": True, "message": message, "data":result}, 200
            else:
                return {"status": False, "message": message, "data":result}, 400
        else:
            result = results
            message = result["responseMessage"]
            return {"status": False, "message": message, "data":result}, 400
api.add_resource(FidelityTestIntraBankREQUERY, '/api/v1/idlfidelitybank/intrabank/enquery/test')



###################################################################
################### TERMII SMS ####################################

TERMII_API_KEY = "TLeGtkb5qj7nvYTgyfPvim5UilNlXaYDmGg3lk7Y7KSRCEtELVXUjT9TIOSqgO"

class TermiiSendSMS(Resource):
    parser = reqparse.RequestParser()

    parser.add_argument('sender',type=str,required=True,help="Enter Sender. Field cannot be left blank")
    parser.add_argument('receiver',type=str,required=True,help="Enter Receiver number. Field cannot be left blank")
    parser.add_argument('message',type=str,required=True,help="Enter Message. Field cannot be left blank")
    
    def post(self):
        data = TermiiSendSMS.parser.parse_args()
        sender = str(data['sender']).upper()
        receiver = str(data['receiver'])
        message = str(data['message'])
        if len(receiver) != 11 or len(''.join(i for i in receiver if i.isdigit())) != 11:
            return {"status": False, "message": "Phone number must be 11 digits"}, 404
        # Set the phone number in international format
        recipients = f"234{receiver[1:]}"
        print(recipients)
        if sender not in ["SAFEPAY", "PLASCHEMA"]:
            return {"status": False, "message": "Invalid SenderID. Please contact admin for assistance.", "data":""},404
        if sender=="SAFEPAY":
            sender = "SafePAY"

        url = "https://api.ng.termii.com/api/sms/send"
        payload = {
                "to": recipients,
                "from": "N-Alert",
                "sms": f"{sender}\n{message}\npowered by Instant Deposit Ltd",
                "type": "plain",
                "channel": "dnd",
                "api_key": TERMII_API_KEY 
            }
        # payload = {
        #         "to": recipients,
        #         "from": sender,
        #         "sms": message,
        #         "type": "plain",
        #         "channel": "generic",
        #         "api_key": TERMII_API_KEY 
        #     }
        headers = {
        'Content-Type': 'application/json',
        }
        response = requests.request("POST", url, headers=headers, json=payload)
        print(response.text)
        e=response.json()
        return {"status": True, "message": e, "data":""}

        # try:
        #     # response = sms.send(message, [recipients], sender)
        #     response = requests.post( url = url, headers = headers, data = data )
        #     r = response.json()
        #     message = r["SMSMessageData"]["Message"].split(" ")[0]
        #     if message.lower() != "sent":
        #         return {"status": False, "message": message, "data":r["SMSMessageData"]}
        #     else:
        #         return {"status": True, "message": "Message sent.", "data":r["SMSMessageData"]}
        # except Exception as e:
        #     return {"status": False, "message": e, "data":""}

api.add_resource(TermiiSendSMS, '/api/client/sms')


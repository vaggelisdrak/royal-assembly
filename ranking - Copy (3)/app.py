from enum import unique
from faulthandler import disable
from io import BytesIO
from fileinput import filename
import json
import re
from flask import Flask, jsonify, redirect, render_template, request, send_file, session, flash, Response, url_for 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import null, true,desc
from flask_msearch import Search
from hashlib import *
from werkzeug.security import generate_password_hash, check_password_hash
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import *
import numpy as np
from werkzeug.utils import secure_filename
import datetime
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from flask_ckeditor import CKEditor
import math


app = Flask(__name__)

ENV = 'dev'

if ENV == 'dev':
    app.debug = True
    app.secret_key = 'hard-to-guess-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///USERS.db'
else:
    app.debug = False
    app.secret_key = os.environ.get('SECRET')
    #app.config['serve_static_files'] = True
    uri = os.environ.get("DATABASE_URL")  # or other relevant config var
    if uri and uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = uri

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['serve_static_files'] = True
#app.config.update(dict(
  #PREFERRED_URL_SCHEME = 'http'
#))

ckeditor = CKEditor(app)

db = SQLAlchemy(app,session_options={"autoflush": False})
search = Search(app)
search.init_app(app)
search.create_index(update=True)
MSEARCH_INDEX_NAME =  os.path.join(app.root_path,'msearch')
MSEARCH_PRIMARY_KEY = 'id'
MSEARCH_ENABLE = True

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view ="login"


@login_manager.user_loader
def load_user(user_id):
    return Users_database.query.get(int(user_id))

class Users_database(db.Model, UserMixin):
    __tablename__ = 'Users_database'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(200), unique=True ,nullable=False)
    email = db.Column(db.String(200), unique=True ,nullable=False)
    password_hash = db.Column(db.String(400), nullable=False)

    #password encyption
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute!')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __init__(self, username, email, password_hash):
        self.username = username
        self.email = email
        self.password_hash = password_hash

#---------------------------------USERS PANEL---------------------------------------------

class USERS_PROFILE_database(db.Model):
    __tablename__ = 'USERS_PROFILE_database'
    __searchable__ =['name','followers','following']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50) ,unique=True, nullable=False)
    filename = db.Column(db.String(50),nullable=True)
    data = db.Column(db.LargeBinary,nullable=True)
    bio = db.Column(db.String(200) ,nullable=True)
    #followers = db.Column(db.String(500) ,nullable=True)
    #following = db.Column(db.String(500) ,nullable=True)
    followers = db.relationship("Followers_database", backref="USERS_PROFILE_database",cascade="all, delete")
    following = db.relationship("Following_database", backref="USERS_PROFILE_database",cascade="all, delete")
    items = db.relationship("ITEMS_database", backref="USERS_PROFILE_database",cascade="all, delete")
    
    def __init__(self, name, filename, data, bio):
        self.name = name
        self.filename = filename
        self.data = data
        self.bio = bio

class Followers_database(db.Model):
    __tablename__ = 'Followers_database'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50) ,nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("USERS_PROFILE_database.id"), nullable=True)

class Following_database(db.Model):
    __tablename__ = 'Following_database'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50) ,nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey("USERS_PROFILE_database.id"), nullable=True)

class ITEMS_database(db.Model): #list each user creates
    __tablename__ = 'ITEMS_database'
    __searchable__ =['name','positiion','highest','lowest']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50) ,nullable=False, unique=True)
    name = db.Column(db.String(50) ,nullable=False, unique=True)
    wins = db.Column(db.Integer,nullable=False)
    loses = db.Column(db.Integer,nullable=False)
    score = db.Column(db.Integer ,nullable=False)
    highest = db.Column(db.Integer,nullable=True)
    lowest = db.Column(db.Integer,nullable=True)
    position = db.Column(db.Integer,nullable=True)
    trend= db.Column(db.Integer,nullable=True)
    filename = db.Column(db.String(50),nullable=True)
    data = db.Column(db.LargeBinary,nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("USERS_PROFILE_database.id"), nullable=True)
    
    def __init__(self, name, wins, loses, score, position, trend,highest,lowest, filename, data):
        self.name = name
        self.wins = wins
        self.loses = loses
        self.score = score
        self.position = position
        self.trend = trend
        self.highest = highest
        self.lowest = lowest
        self.filename = filename
        self.data = data

#---------------------------------ADMIN PANEL----------------------------------------------

class MAIN_database(db.Model):
    __tablename__ = 'MAIN_database'
    __searchable__ =['name','wins','loses','score','positiion','highest','lowest']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50) ,nullable=False, unique=True)
    wins = db.Column(db.Integer,nullable=False)
    loses = db.Column(db.Integer,nullable=False)
    score = db.Column(db.Integer ,nullable=False)
    highest = db.Column(db.Integer,nullable=True)
    lowest = db.Column(db.Integer,nullable=True)
    position = db.Column(db.Integer,nullable=True)
    trend= db.Column(db.Integer,nullable=True)
    filename = db.Column(db.String(50),nullable=True)
    data = db.Column(db.LargeBinary,nullable=True)
    
    def __init__(self, name, wins, loses, score, position, trend,highest,lowest, filename, data):
        self.name = name
        self.wins = wins
        self.loses = loses
        self.score = score
        self.position = position
        self.trend = trend
        self.highest = highest
        self.lowest = lowest
        self.filename = filename
        self.data = data

class History_database(db.Model):
    __tablename__ = 'History_database'
    __searchable__ =['name','fromm','too','date']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50) ,nullable=False)
    fromm = db.Column(db.Integer,nullable=False)
    too = db.Column(db.Integer,nullable=False)
    date = db.Column(db.String(50) ,nullable=False)
    
    def __init__(self, name, fromm, too, date):
        self.name = name
        self.fromm = fromm
        self.too = too
        self.date = date

class USERS_HISTORY_database(db.Model):
    __tablename__ = 'USERS_HISTORY_database'
    __searchable__ =['name','fromm','too','date']
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50) ,nullable=False, unique=True)
    date = db.Column(db.String(50) ,nullable=False)
    
    def __init__(self, name, date):
        self.name = name
        self.date = date

#---------------------------------TOURNAMENTS----------------------------------------------

'''class TOURNAMENTS_database(db.Model):
    __tablename__ = 'TOURNAMENTS_database'
    id = db.Column(db.Integer, primary_key=True)
    tour = db.relationship("TOUR_database", backref="TOURNAMENTS_database",cascade="all, delete")'''

class TOUR_database(db.Model):
    __tablename__ = 'TOUR_database'
    __searchable__ =['tour_name']
    id = db.Column(db.Integer, primary_key=True)
    tour_name = db.Column(db.String(50) ,nullable=False, unique=True)
    players = db.relationship("TOUR_PLAYERS_database", backref="TOUR_database",cascade="all, delete")
    #parent_id = db.Column(db.Integer, db.ForeignKey("TOURNAMENTS_database.id"), nullable=True)

class TOUR_PLAYERS_database(db.Model):
    __tablename__ = 'TOUR_PLAYERS_database'
    __searchable__ =['username','wins','loses','positiion']
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50) ,nullable=False)
    wins = db.Column(db.Integer,nullable=True)
    loses = db.Column(db.Integer,nullable=True)
    position = db.Column(db.Integer,nullable=True)
    round = db.Column(db.Integer,nullable=True)
    filename = db.Column(db.String(50),nullable=True)
    data = db.Column(db.LargeBinary,nullable=True)
    player_rounds = db.relationship("STANDINGS_database", backref="TOUR_PLAYERS_database",cascade="all, delete")
    parent_id = db.Column(db.Integer, db.ForeignKey("TOUR_database.id"), nullable=True)

class STANDINGS_database(db.Model):
    __tablename__ = 'STANDINGS_database'
    __searchable__ =['username','wins','loses','positiion']
    id = db.Column(db.Integer, primary_key=True)
    first_round_score = db.Column(db.Integer,nullable=True)
    second_round_score = db.Column(db.Integer,nullable=True)
    third_round_score = db.Column(db.Integer,nullable=True)
    fourth_round_score = db.Column(db.Integer,nullable=True)
    fifth_round_score = db.Column(db.Integer,nullable=True)
    sixth_round_score = db.Column(db.Integer,nullable=True)
    seventh_round_score = db.Column(db.Integer,nullable=True)
    eigth_round_score = db.Column(db.Integer,nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("TOUR_PLAYERS_database.id"), nullable=True)


#---------------------------------BLOG DATABASE----------------------------------------------

class BLOG_database(db.Model):
    __tablename__ = 'BLOG_database'
    __searchable__ =['title','topic','tags','article']
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(50),nullable=False)
    topic = db.Column(db.String(50),nullable=False)
    tags = db.Column(db.String(100),nullable=True)
    filename = db.Column(db.String(100),nullable=True)
    data = db.Column(db.LargeBinary,nullable=True)
    article = db.Column(db.String(5000),nullable=False)

    def __init__(self, title, topic, tags, filename, data, article):
        self.title = title
        self.topic = topic
        self.tags = tags
        self.filename = filename
        self.data = data
        self.article = article
        

#---------------------------------FILE DATABASE----------------------------------------------

class Files_database(db.Model):
    __tablename__ = 'Files_database'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(100))
    data = db.Column(db.LargeBinary)
    status = db.Column(db.String(50))

    def __init__(self, filename, data,status):
        self.filename = filename
        self.data = data
        self.status = status

#--------------------------------------Homepage-----------------------------------------------

@app.route('/')
def index():
    n = session.get('nnum')
    f = open("keyword.txt", "r+")
    s=f.read()
    f.truncate(0)
    f.close()

    print(s)
    if s:
        players = MAIN_database.query.msearch(s,fields=['name','position']).all()
    else:
        if n:
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(int(n)).all()
        else:
            n=10
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(10).all()

    #blogs
    articles = BLOG_database.query.all()

    #today's winners and losers
    dt = datetime.datetime.today()
    date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
    print("date is",date)
    players_history = History_database.query.filter_by(date=date).all() #all players who moved seeds today
    players_names = []
    for i in players_history:
        players_names.append(i.name)

    print(players_names)
    winners = MAIN_database.query.filter(MAIN_database.name.in_(players_names)).order_by(MAIN_database.trend.desc()).limit(4).all()
    losers = MAIN_database.query.filter(MAIN_database.name.in_(players_names)).order_by(MAIN_database.trend.asc()).limit(4).all()
    print(winners)
    print(losers)

    #all users 
    all_users = USERS_PROFILE_database.query.all()

    return render_template('index.html',players=players,n=n,articles=articles,winners=winners,losers=losers,all_users = all_users)

@app.route('/ssearch', methods=['POST','GET'])
def ssearch():
    if request.method == 'POST':
        s = request.form.get('search')
        num = request.form.get('num')
        if not s :
            if num:
                session['nnum']=num
            else:
                session['nnum']=10
        else:
            f = open("keyword.txt", "w")
            f.write(str(s))
            f.close()

            if num:
                session['nnum']=num
            else:
                session['nnum']=10
        return redirect('/#popular')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        conf_password = request.form.get('conf_password')
        print(username,email,password,conf_password)

        #confirm password
        if password!=conf_password:
            flash("The passwords don't match!",'error')
            return redirect('/#value')

        #check if username and email are unique

        #users = []
        u = Users_database.query.all()
        for g in u:
            #users.append((g.username,g.email))
            if g.username == username:
                flash("This username isn't available!",'error')
                return redirect('/#value')
            if g.email == email:
                flash("This email isn't available!",'error')
                return redirect('/#value')

        #add new user to the database
        
        password = generate_password_hash(password,"sha256")
        user = Users_database(username=username ,email=email,password_hash=password)
        db.session.add(user)
        db.session.commit()
        flash("Account registered!",'success')
        return redirect('/#value')

@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(email,password)
        u = Users_database.query.all()
        for g in u:
            if g.email == email:
                #check the hash
                user = Users_database.query.filter_by(email=email).first()
                if check_password_hash(user.password_hash, password):
                    login_user(user)
                    flash("You have successfully logged in",'success')
                    print(user.username)
                    username = user.username
                    print('logged in')

                    #session
                    session['user'] = username
                    session['email'] = email
                    
                    if username =="admin":
                        return redirect('/admin')
                    else:
                        return redirect('/dashboard/'+str(username))
                else:
                    flash("The password is incorrect!",'error')
                    return redirect('/#value')
        else:
            #flash("This user doesn't exist!",'error')
            return redirect('/')

@app.route('/logout', methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    flash("You have been logged out")
    return redirect('/')

@app.route('/blogs',methods=['POST','GET'])
def blogs():
    if request.method == 'POST':
        s = request.form.get('search')
        num = request.form.get('num')
        articles = BLOG_database.query.msearch(s,fields=['title','topic','tags','article']).all()
        return render_template('blogs.html',articles=articles)
    else:
        articles = BLOG_database.query.all()
        return render_template('blogs.html',articles=articles)

#------------------------------------USERS----------------------------------------------------------------------------------------------------------------------------------------

@app.route('/dashboard/<string:user>', methods=['POST','GET'])
@login_required
def dashboard(user):
    profile = USERS_PROFILE_database(name=user,filename=None,data=None,bio=None)
    profiles = USERS_PROFILE_database.query.all()

    def profile_exists():
        for i in profiles:
            if i.name == user:
                return True

    if profile_exists() != True:
        db.session.add(profile)
        db.session.commit()

    profile = USERS_PROFILE_database.query.filter_by(name=user).first()
    return render_template('dashboard.html',user = user, profile = profile)

@app.route('/downloaddd/<string:filename>')
def downloaddd(filename):
    upload = USERS_PROFILE_database.query.filter_by(filename=filename).first()
    print(upload)
    return send_file(BytesIO(upload.data),download_name=upload.filename, as_attachment=True)

@app.route('/updateaccount/<string:user>', methods=['POST','GET'])
@login_required
def updateaccount(user):
    profile = USERS_PROFILE_database.query.filter_by(name=user).first()
    if request.method == 'POST':
        print(user)
        name = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        bio = request.form.get('biography')
        image = request.files.get('image')
        #job_ad = JOB_ADS_database.query.filter_by(phone_number=phone_number).first()
        #if not job_ad:
        user_to_update = Users_database.query.filter_by(username=user).first() #account of each user
        users = Users_database.query.all()

        if user_to_update:
            if name:
                for g in users:
                    if g.username == name and g.id!=user_to_update.id:
                        print('name exists')
                        flash("Name already exists!",'error')
                        return redirect('/updateaccount/'+str(user_to_update.username))
                user_to_update.username = name
            if email:
                for g in users:
                    if g.email == email and g.id!=user_to_update.id:
                        print('email exists')
                        flash("Email already exists!",'error')
                        return redirect('/updateaccount/'+str(user_to_update.username))
                user_to_update.email = email

            if password:
                password = generate_password_hash(password,"sha256")
                user_to_update.password_hash = password

            db.session.flush()

            profile_to_update = USERS_PROFILE_database.query.filter_by(name=user).first() #profile of each user
            if name:
                profile_to_update.name = name

            if bio:
                profile_to_update.bio = bio

            if image:
                profile_to_update.filename=image.filename
                profile_to_update.data=image.read()
            db.session.commit()

        flash("Your account is updated!",'success')
        #return redirect('/dashboard/'+str(user_to_update.username))
        return redirect('/updateaccount/'+str(user_to_update.username))
    
    user = Users_database.query.filter_by(username=user).first()
    return render_template('updateaccount.html',user = user,profile=profile)

@app.route('/view_users/<string:user>',methods=['POST','GET'])
@login_required
def view_users(user):
    all_users = USERS_PROFILE_database.query.filter(USERS_PROFILE_database.name!=user).all()
    user = USERS_PROFILE_database.query.filter_by(name=user).first()
    return render_template('view_users.html',all_users=all_users,user=user.name)

@app.route('/follow/<string:user>,<string:username>',methods=['POST','GET'])
@login_required
def follow(user,username):
    if request.method =='POST':

        #followed user
        followed_user = USERS_PROFILE_database.query.filter_by(name=username).first()
        followers = Followers_database(username=user, parent_id=followed_user.id)
        db.session.add(followers)
        db.session.commit()

        #user who clicked follow
        following_user = USERS_PROFILE_database.query.filter_by(name=user).first()
        following = Following_database(username=username, parent_id=following_user.id)
        db.session.add(following)
        db.session.commit()

        all_users = USERS_PROFILE_database.query.filter(USERS_PROFILE_database.name!=user).all()
        #return render_template('view_users.html',all_users=all_users,followed=followed)
        return redirect('/view_users/'+str(user))

    all_users = USERS_PROFILE_database.query.filter(USERS_PROFILE_database.name!=user).all()
    user = USERS_PROFILE_database.query.filter_by(name=user).first()
    return render_template('view_users.html',all_users=all_users,user=user.name)

@app.route('/unfollow/<string:user>,<string:username>',methods=['POST','GET'])
@login_required
def unfollow(user,username):
    if request.method =='POST':
        print('unfollow\n\n')
        #unfollowed user
        followed_user = USERS_PROFILE_database.query.filter_by(name=username).first()
        followers = Followers_database.query.filter_by(username=user, parent_id=followed_user.id).first()
        db.session.delete(followers)
        db.session.commit()

        #user who clicked unfollow
        following_user = USERS_PROFILE_database.query.filter_by(name=user).first()
        following = Following_database.query.filter_by(username=username, parent_id=following_user.id).first()
        db.session.delete(following)
        db.session.commit()

        all_users = USERS_PROFILE_database.query.filter(USERS_PROFILE_database.name!=user).all()
        #return render_template('view_users.html',all_users=all_users,followed=followed)
        return redirect('/view_users/'+str(user))

    all_users = USERS_PROFILE_database.query.filter(USERS_PROFILE_database.name!=user).all()
    user = USERS_PROFILE_database.query.filter_by(name=user).first()
    return render_template('view_users.html',all_users=all_users,user=user.name)

#---------------------------------------ADMIN------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/admin', methods=['POST','GET'])
@login_required
def admin():
    n = session.get('num')
    f = open("keyword.txt", "r+")
    s=f.read()
    f.truncate(0)
    f.close()

    print(s)
    if s:
        players = MAIN_database.query.msearch(s,fields=['name','position']).all()
    else:
        if n:
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(int(n)).all()
        else:
            n=10
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(10).all()

    changes = History_database.query.order_by(History_database.id.desc()).limit(15).all()
    print(players)

    tournaments = TOUR_database.query.all()
    return render_template('admin.html',players=players,changes=changes,n=n,tournaments=tournaments)

@app.route('/admin_search', methods=['POST','GET'])
@login_required
def admin_search():
    if request.method == 'POST':
        s = request.form.get('search')
        num = request.form.get('num')
        if not s :
            if num:
                session['num']=num
            else:
                session['num']=10
        else:
            f = open("keyword.txt", "w")
            f.write(str(s))
            f.close()

            if num:
                session['num']=num
            else:
                session['num']=10
        return redirect('/admin')

@app.route('/_autocomplete', methods=['GET'])
def autocomplete():
    players = MAIN_database.query.all()
    p = []
    for i in players:
        p.append(i.name)
    #print(p)
    return Response(json.dumps(p), mimetype='application/json')

def change_position(name,fromm,too):
    user_to_update = MAIN_database.query.filter_by(name=name).first()
    x = int(fromm) - int(too)

    if x > 0: #move up
        total_players = MAIN_database.query.all()
        for i in total_players:
            '''if int(i.position) < int(fromm) and int(i.position) >= int(too):
                #i.position = int(i.position)+1
                if i.trend>0:
                    i.trend = -1
                else:
                    i.trend-=1
                db.session.commit()'''

        if user_to_update.trend<0:
            user_to_update.trend = abs(x)      
            db.session.commit()
        else:
            user_to_update.trend += x
            db.session.commit()

    elif x < 0: #move down
        total_players = MAIN_database.query.all()
        for i in total_players:
            '''if int(i.position) > int(fromm) and int(i.position) <= int(too):
                #i.position = int(i.position)-1
                if i.trend<0:
                    i.trend = 1
                else:
                    i.trend+=1
                db.session.commit()'''

        if user_to_update.trend>0:
            user_to_update.trend = x
            db.session.commit()
        else:
            user_to_update.trend += x
            db.session.commit()

    else: #same 
        pass
    
    user_to_update.position = too
    if int(user_to_update.position) < int(user_to_update.highest):
        user_to_update.highest = user_to_update.position
    if int(user_to_update.position) > int(user_to_update.lowest):
        user_to_update.lowest = user_to_update.position
    db.session.commit()

    #Add changes to history
    dt = datetime.datetime.today()
    date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
    print("date is",date)
    player = History_database(name=user_to_update.name,fromm=fromm,too=too,date=date)
    db.session.add(player)
    db.session.commit()

@app.route('/updateList',methods=['POST','GET'])
def updateList():
    if request.method == 'POST':
        players = MAIN_database.query.all()
        l=len(players)
        print('l',l)

        orders = request.form['order']
        print(orders.split(','))
        changes = []

        for i in orders.split(','):
            if i:
                changes.append(i)
        print(changes)

        new_changed = []
        new_changed = [changes[i:i + 2] for i in range(0, len(changes), 2)]
        #print(new_changed)

        k=0
        for i in new_changed:
            k+=1
            i.append(str(k))

        print(new_changed)

        for i in new_changed:
            if i[1] != i[2]:
                change_position(i[0],int(i[1]),int(i[2]))
                #return redirect('/admin')

    return redirect('/admin#list')

@app.route('/add', methods=['POST','GET'])
@login_required
def add():
    if request.method == 'POST':
        name = request.form.get('username')
        wins = request.form.get('wins')
        loses = request.form.get('loses')
        score = request.form.get('score')
        position = request.form.get('position')
        print("pos",position)
        image = request.files.get('image')
        trend = 0
        highest =0
        lowest =0

        if not wins:
            wins =0
        if not loses:
            loses =0
        if not score:
            score=0

        player = MAIN_database.query.filter_by(name=name).first()

        if not player:
            if position:
                player = MAIN_database(name=name, wins=wins, loses=loses, score = score, position = position ,highest=highest,lowest=lowest,trend=trend, filename=image.filename,data=image.read())
                db.session.add(player)
                db.session.commit()

                total_players = MAIN_database.query.all()
                l=1
                for i in total_players:
                    l+=1
                fromm = l
                too = position

                #change pos auto after adding player
                x = int(fromm) - int(too)

                if x > 0: #move up
                    total_players = MAIN_database.query.all()
                    for i in total_players:
                        if int(i.position) < int(fromm) and int(i.position) >= int(too):
                            i.position = int(i.position)+1
                            if i.trend>0:
                                i.trend = -1
                            else:
                                i.trend-=1
                            db.session.commit()

                    if player.trend<0:
                        player.trend = abs(x)      
                        db.session.commit()
                    else:
                        player.trend += x
                        db.session.commit()

                elif x < 0: #move down
                    total_players = MAIN_database.query.all()
                    for i in total_players:
                        if int(i.position) > int(fromm) and int(i.position) <= int(too):
                            i.position = int(i.position)-1
                            if i.trend<0:
                                i.trend = 1
                            else:
                                i.trend+=1
                            db.session.commit()

                    if player.trend>0:
                        player.trend = x
                        db.session.commit()
                    else:
                        player.trend += x
                        db.session.commit()

                else: #same 
                    pass
                
                player.position = too
                #new players trend is 0 (so new)
                player.trend = 0
                db.session.commit()

                dt = datetime.datetime.today()
                date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
                print("date is",date)
                user = History_database(name=player.name,fromm=fromm,too=too,date=date)
                db.session.add(user)
                db.session.commit()

                flash("You have successfully added the player",'success')
                return redirect('/admin')
            else:
                total_players = MAIN_database.query.all()
                l=1
                for i in total_players:
                    l+=1
                player = MAIN_database(name=name, wins=wins, loses=loses, score = score, position = l ,highest=highest,lowest=lowest,trend=trend, filename=image.filename,data=image.read())
                db.session.add(player)
                db.session.commit()

                dt = datetime.datetime.today()
                date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
                print("date is",date)
                player = History_database(name=player.name,fromm=0,too=0,date=date)
                db.session.add(player)
                db.session.commit()
                flash("You have successfully added the player to the bottom of the list",'success')
                return redirect('/admin')
        else:
            flash("Username already exists",'error')
            return redirect('/admin')
    else:
        return redirect('/admin')

@app.route('/change_pos', methods=['GET','POST'])
@login_required
def change_pos():
    if request.method == 'POST':
        name = request.form.get('username')
        #fromm = request.form.get('from')
        too = request.form.get('to')
        print(too)

        user_to_update = MAIN_database.query.filter_by(name=name).first()
        fromm = user_to_update.position
        if user_to_update and int(fromm) == int(user_to_update.position) and int(fromm)>0 and int(too)>0:
            x = int(fromm) - int(too)

            if x > 0: #move up
                total_players = MAIN_database.query.all()
                for i in total_players:
                    if int(i.position) < int(fromm) and int(i.position) >= int(too):
                        i.position = int(i.position)+1

                        if int(i.position) < int(i.highest):
                            i.highest = i.position
                        if int(i.position) > int(i.lowest):
                            i.lowest = i.position

                        if i.trend>0:
                            i.trend = -1
                        else:
                            i.trend-=1
                        db.session.commit()

                if user_to_update.trend<0:
                    user_to_update.trend = abs(x)      
                    db.session.commit()
                else:
                    user_to_update.trend += x
                    db.session.commit()

            elif x < 0: #move down
                total_players = MAIN_database.query.all()
                for i in total_players:
                    if int(i.position) > int(fromm) and int(i.position) <= int(too):
                        i.position = int(i.position)-1

                        if int(i.position) < int(i.highest):
                            i.highest = i.position
                        if int(i.position) >  int(i.lowest):
                            i.lowest = i.position

                        if i.trend<0:
                            i.trend = 1
                        else:
                            i.trend+=1
                        db.session.commit()

                if user_to_update.trend>0:
                    user_to_update.trend = x
                    db.session.commit()
                else:
                    user_to_update.trend += x
                    db.session.commit()

            else: #same 
                pass
            
            user_to_update.position = too
            if int(user_to_update.position) < int(user_to_update.highest):
                user_to_update.highest = user_to_update.position
            if int(user_to_update.position) > int(user_to_update.lowest):
                user_to_update.lowest = user_to_update.position
            db.session.commit()

            #Add changes to history
            dt = datetime.datetime.today()
            date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
            print("date is",date)
            player = History_database(name=user_to_update.name,fromm=fromm,too=too,date=date)
            db.session.add(player)
            db.session.commit()

            return redirect('/admin')
        else:
            flash("Player was not found",'error')
            return redirect('/admin')
            
    else:
        flash("Wrong inputs",'error')
        return redirect('/admin')

@app.route('/download/<string:filename>')
def download(filename):
    upload = MAIN_database.query.filter_by(filename=filename).first()
    print(upload)
    return send_file(BytesIO(upload.data),download_name=upload.filename, as_attachment=True)

@app.route('/edit/<int:id>', methods=['GET','POST'])
@login_required
def edit(id):
    if request.method == 'POST':
        name = request.form.get('username')
        wins = request.form.get('wins')
        loses = request.form.get('loses')
        score = request.form.get('score')
        image = request.files.get('image')

        #job_ad = JOB_ADS_database.query.filter_by(phone_number=phone_number).first()
        #if not job_ad:
        user_to_update = MAIN_database.query.filter_by(id=id).first()

        if user_to_update:
            user_to_update.name = name
            user_to_update.wins = wins
            user_to_update.loses = loses
            user_to_update.score = score
            user_to_update.position = user_to_update.position

            if image:
                user_to_update.filename=image.filename
                user_to_update.data=image.read()
            db.session.commit()
            flash("You have successfully updated the player",'success')
            i = MAIN_database.query.filter_by(id=id).first()
            print(i)
            return render_template('update.html',i=i)
    else:
        i = MAIN_database.query.filter_by(id=id).first()
        print(i)
        return render_template('update.html',i=i)

@app.route('/delete/<int:id>')
@login_required
def delete(id):
    del_pl= MAIN_database.query.get_or_404(id)
    p = del_pl.position

    dt = datetime.datetime.today()
    date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
    print("date is",date)
    player = History_database(name=del_pl.name,fromm=p,too=0,date=date)
    db.session.add(player)
    db.session.commit()
    try:
        db.session.delete(del_pl)
        db.session.commit()

        players = MAIN_database.query.all()
        for i in players:
            if int(i.position) > p:
                fromm = i.position
                i.position -=1
                if i.trend<0:
                    i.trend = 1
                else:
                    i.trend+=1
                db.session.commit()
                dt = datetime.datetime.today()
                date = str(dt.month) +"-"+ str(dt.day) +"-"+ str(dt.year)
                print("date is",date)
                player = History_database(name=i.name,fromm=fromm,too=i.position,date=date)
                db.session.add(player)
                db.session.commit()
        return redirect('/admin')
    except:
        return "<h1>ERROR 404</h1>"

@app.route('/clear')
@login_required
def clear():
    '''h = History_database.query.all()
    for i in h:
        db.session.delete(i)
        db.session.commit()'''
    db.session.query(History_database).delete()
    db.session.commit()
    return redirect('/admin')

#--------------------------ADMIN - BLOG-------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/view_blog',methods=['POST','GET'])
@login_required
def view_blog():
    if request.method == 'POST':
        s = request.form.get('search')
        num = request.form.get('num')
        tags=[]
        articles = BLOG_database.query.all()
        for i in articles:
            tags.append(i.tags)
        articles = BLOG_database.query.msearch(s,fields=['title','topic','tags','article']).all()
        return render_template('view_blog.html',articles=articles,tags=tags)
    else:
        articles = BLOG_database.query.all()
        tags=[]
        for i in articles:
            tags.append(i.tags)
        return render_template('view_blog.html',articles=articles,tags=tags)

@app.route('/downloadd/<string:filename>')
def downloadd(filename):
    upload = BLOG_database.query.filter_by(filename=filename).first()
    print(upload)
    return send_file(BytesIO(upload.data),download_name=upload.filename, as_attachment=True)

@app.route('/add_blog', methods =['POST','GET'])
@login_required
def add_blog():
    if request.method == 'POST':
        title = request.form.get('title')
        topic = request.form.get('topic')
        tags = request.form.get('tags')
        image = request.files.get('image')
        article = request.form.get('ckeditor')

        blog_post = BLOG_database(title=title,topic=topic,tags=tags,filename=image.filename,data=image.read(),article=article)
        db.session.add(blog_post)
        db.session.commit()
        return redirect('/view_blog')
    return render_template('add_blog.html')

@app.route('/edit_blog/<int:id>', methods =['POST','GET'])
@login_required
def edit_blog(id):
    blog_post = BLOG_database.query.filter_by(id=id).first()
    if request.method == 'POST':
        title = request.form.get('title')
        topic = request.form.get('topic')
        tags = request.form.get('tags')
        image = request.files.get('image')
        article = request.form.get('ckeditor')

        print(title)

        blog_post = BLOG_database.query.filter_by(id=id).first()
        blog_post.title = title
        blog_post.topic = topic
        blog_post.tags = tags
        if image:
            blog_post.filename = image.filename
            blog_post.data = image.read()
        blog_post.article = article
        db.session.commit()
        flash("You have successfully updated the blog",'success')
        return redirect('/view_blog')

    return render_template('edit_blog.html',blog_post=blog_post)

@app.route('/delete_blog/<int:id>', methods =['POST','GET'])
@login_required
def delete_blog(id):
    blog_post = BLOG_database.query.filter_by(id=id).first()
    db.session.delete(blog_post)
    db.session.commit()
    return redirect('/view_blog')

#--------------------------ADMIN - MANAGE USERS-------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/manage_users')
@login_required
def manage_users():
    users = Users_database.query.filter(Users_database.username!='admin').order_by(Users_database.id.desc()).all()
    return render_template('manage_users.html',users=users)

#--------------------------ADMIN - CREATE TOURNAMENT------------------------------------------------------------------------------------------------------------------------------------------------- 
@app.route('/create_tournament')
@login_required
def create_tournament():
    n = session.get('num')
    f = open("keyword.txt", "r+")
    s=f.read()
    f.truncate(0)
    f.close()

    print(s)
    if s:
        players = MAIN_database.query.msearch(s,fields=['name','position']).all()
    else:
        if n:
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(int(n)).all()
        else:
            n=10
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(10).all()

    return render_template('create_tournament.html',players=players)


@app.route('/name_tour',methods =['POST','GET'])
@login_required
def name_tour():
    if request.method == 'POST':
        name = request.form.get('tour_name')

        #check if name already exists
        tours = TOUR_database.query.all()
        for t in tours:
            if t.tour_name == name:
                flash('Tournament name already exists')
                return redirect('/create_tournament')

        new_tour = TOUR_database(tour_name = name)
        db.session.add(new_tour)
        db.session.commit()

        '''tour_players = TOUR_PLAYERS_database.query.all()
        for p in tour_players:
            p.parent_id = new_tour.id
            
        db.session.commit()'''
        tour_name = name
        return redirect('/create_tournament2/'+str(tour_name))


@app.route('/create_tournament2/<string:tour_name>')
@login_required
def create_tournament2(tour_name):
    n = session.get('num')
    f = open("keyword.txt", "r+")
    s=f.read()
    f.truncate(0)
    f.close()

    print(s)
    if s:
        players = MAIN_database.query.msearch(s,fields=['name','position']).all()
    else:
        if n:
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(int(n)).all()
        else:
            n=10
            players = MAIN_database.query.order_by(MAIN_database.position.asc()).limit(10).all()

    tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
    tour_players = TOUR_PLAYERS_database.query.order_by(TOUR_PLAYERS_database.position.asc()).filter_by(parent_id=tournament.id).all()

    return render_template('create_tournament2.html',players=players,tour_players=tour_players,tour_name=tour_name)

@app.route('/add_to_list/<string:name>,<int:pos>,<string:tour_name>',methods =['POST','GET'])
@login_required
def add_to_list(name,pos,tour_name):
    if request.method == 'POST':
        print(name)
        tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
        p = MAIN_database.query.filter_by(name=name).first()
        player = TOUR_PLAYERS_database(username=name,wins=0,loses=0,position=pos,filename=p.filename,data=p.data,parent_id=tournament.id)
        db.session.add(player)
        db.session.commit()

        return redirect('/create_tournament2/'+str(tour_name))

@app.route('/add_to_listt/<string:tour_name>',methods =['POST','GET'])
@login_required
def add_to_listt(tour_name):
    if request.method == 'POST':
        name = request.form.get('username')
        pos = request.form.get('position')
        image = request.files.get('image')

        tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
        #p = MAIN_database.query.filter_by(name=name).first()
        player = TOUR_PLAYERS_database(username=name,wins=0,loses=0,position=pos,filename=image.filename,data=image.read(),parent_id=tournament.id)
        db.session.add(player)
        db.session.commit()

        return redirect('/create_tournament2/'+str(tour_name))

@app.route('/remove_from_list/<string:name>,<string:tour_name>',methods =['POST','GET'])
@login_required
def remove_from_list(name,tour_name):
    if request.method == 'POST':
        print(name)
        tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
        player = TOUR_PLAYERS_database.query.filter_by(username=name, parent_id=tournament.id).first()
        db.session.delete(player)
        db.session.commit()

        return redirect('/create_tournament2/'+str(tour_name))

@app.route('/view_tournament/<string:tour_name>')
@login_required
def view_tournament(tour_name):
    tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
    players = TOUR_PLAYERS_database.query.filter_by(parent_id=tournament.id).all()

    total_players = 0
    pair1 = []
    pair2 = []
    for p in players:
        total_players+=1
        pair1.append(p.username)
        pair2.append(p.username)
        
    print(total_players)

    faseis = int(math.log2(total_players))
    print(faseis)

    next_round_player = ''
    player_pairs = []
    if total_players%2==0:
        pair2.reverse()
        #print(pair1)
        #print(pair2)
        pairs = list(zip(pair1,pair2))
    else:
        next_round_player = pair1[0]
        pair1.pop(0)
        pair2.reverse()
        pair2.pop()
        #print(pair1)
        #print(pair2)
        pairs = list(zip(pair1,pair2))

    a = int(total_players/2)
    print(pairs[0:a])
    player_pairs = pairs[0:a]

    scores = []
    #first phase
    for i in player_pairs:
        print('i',i)
        
        try:
            player1 = TOUR_PLAYERS_database.query.filter_by(username=i[0],parent_id = tournament.id).first()
            score1 = STANDINGS_database.query.filter_by(parent_id = player1.id).first()
            print(score1.first_round_score)
            #print(player1.player_rounds[0].first_round_score)
            
            player2 = TOUR_PLAYERS_database.query.filter_by(username=i[1],parent_id = tournament.id).first()
            score2 = STANDINGS_database.query.filter_by(parent_id = player2.id).first()
            print(score2.first_round_score)
            #print(player2.player_rounds[0].first_round_score)

            #scores.append((player1.player_rounds[0].first_round_score,player2.player_rounds[0].first_round_score))
            scores.append((score1.first_round_score,score2.first_round_score))
        except:
            scores.append((0,0))
 
    print('scores',scores)

    if faseis==2:
        sscores = []
        second_round_player_pairs = []
        for i in players:
            print('i',i)
            
            pplayer1 = TOUR_PLAYERS_database.query.filter_by(username=i.username,parent_id = tournament.id).first()
            sscore1 = STANDINGS_database.query.filter_by(parent_id = pplayer1.id).first()
            
            print(sscore1.second_round_score)
            if sscore1.second_round_score == null:
                print('ben')
                continue
            #print(player1.player_rounds[0].first_round_score)
            
            #scores.append((player1.player_rounds[0].first_round_score,player2.player_rounds[0].first_round_score))
            sscores.append(sscore1.second_round_score)
            print(pplayer1.username)
            second_round_player_pairs.append(pplayer1.username)
 
        print('scores',sscores)
        print(second_round_player_pairs)
        sec_round = []
       
        sec_round.append((second_round_player_pairs[0],second_round_player_pairs[1]))
        print('sec_round',sec_round)

    return render_template('view_tournament.html',tour_name=tour_name,total_players=total_players,player_pairs=player_pairs,sec_round=sec_round,sscores=sscores,
    next_round_player=next_round_player,faseis=faseis,scores = scores)

@app.route('/update_brackets/<string:tour_name>',methods =['POST','GET'])
@login_required
def update_brackets(tour_name):
    if request.method == 'POST':
        tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
        players = TOUR_PLAYERS_database.query.filter_by(parent_id=tournament.id).all()

        total_players = 0
        pair1 = []
        pair2 = []
        for p in players:
            total_players+=1
            pair1.append(p.username)
            pair2.append(p.username)

        next_round_player = ''
        player_pairs = []
        if total_players%2==0:
            pair2.reverse()
            pairs = list(zip(pair1,pair2))
        else:
            next_round_player = pair1[0]
            pair1.pop(0)
            pair2.reverse()
            pair2.pop()
            pairs = list(zip(pair1,pair2))

        a = int(total_players/2)
        player_pairs = pairs[0:a]


        # first phase

        req = []
        j =0
        for i in player_pairs:
            req.append((i[0],request.form.get(i[0]))) #get score of first player in pair
            req.append((i[1],request.form.get(i[1]))) #get score of second player in pair
            j+=1

        for k in req:
            print('ben')
            print(k,end='\n')
            player = TOUR_PLAYERS_database.query.filter_by(username=k[0],parent_id=tournament.id).first()
            print(int(k[1]),player.id)
            score = STANDINGS_database.query.filter(STANDINGS_database.parent_id == player.id and STANDINGS_database.first_round_score!=null).first()
            #print(score.first_round_score)
            if not score:
                score1_update = STANDINGS_database(first_round_score=int(k[1]),parent_id = player.id)
                db.session.add(score1_update)
                db.session.commit()
            else:
                score.first_round_score = int(k[1])
                db.session.commit()

        '''#second phase-----------------------------------------------------------------------------------------------------------------------
        faseis = int(math.log2(total_players))
        print(faseis)

        second_round_players = []
        if faseis>1:
            
            print('req',req)
            print('players pairs',player_pairs)
            for i in player_pairs:
                for j in req:
                    if j[0] == i[0]:
                        score1 = int(j[1])
                    if j[0] == i[1]:
                        score2 = int(j[1])
                if score1 > score2:
                    second_round_players.append(i[0])
                else:
                    second_round_players.append(i[1])

        print('second round p',second_round_players)

        for p in second_round_players:
            print(p)
            player = TOUR_PLAYERS_database.query.filter_by(username=p,parent_id=tournament.id).first()
            print(int(k[1]),player.id)
            score = STANDINGS_database.query.filter(STANDINGS_database.parent_id == player.id and STANDINGS_database.first_round_score!=null).first()
            score.second_round_score = 0
            db.session.commit()'''

        return redirect('/view_tournament/'+str(tour_name))


@app.route('/update_brackets2/<string:tour_name>',methods =['POST','GET'])
@login_required
def update_brackets2(tour_name):
    if request.method == 'POST':
        tournament = TOUR_database.query.filter_by(tour_name=tour_name).first()
        players = TOUR_PLAYERS_database.query.filter_by(parent_id=tournament.id).all()

        total_players = 0
        pair1 = []
        pair2 = []
        for p in players:
            total_players+=1
            pair1.append(p.username)
            pair2.append(p.username)

        next_round_player = ''
        player_pairs = []
        if total_players%2==0:
            pair2.reverse()
            pairs = list(zip(pair1,pair2))
        else:
            next_round_player = pair1[0]
            pair1.pop(0)
            pair2.reverse()
            pair2.pop()
            pairs = list(zip(pair1,pair2))

        a = int(total_players/2)
        player_pairs = pairs[0:a]


        # first phase

        req = []
        j =0
        for i in player_pairs:
            try:
                req.append((i[0],request.form.get(i[0]))) #get score of first player in pair
                req.append((i[1],request.form.get(i[1]))) #get score of second player in pair
            except:
                pass
            j+=1

        for f in req:#remove other players (only the finalists)
            if not f[1]:
                req.remove(f)
        print(req)

        for k in req:
            print(k,end='\n')
            player = TOUR_PLAYERS_database.query.filter_by(username=k[0],parent_id=tournament.id).first()
            print(int(k[1]),player.id)
            score = STANDINGS_database.query.filter(STANDINGS_database.parent_id == player.id and STANDINGS_database.first_round_score!=null).first()
            #print(score.first_round_score)
            if not score:
                score1_update = STANDINGS_database(second_round_score=int(k[1]),parent_id = player.id)
                db.session.add(score1_update)
                db.session.commit()
            else:
                score.second_round_score = int(k[1])
                db.session.commit()

        return redirect('/view_tournament/'+str(tour_name))



if __name__ == '__main__':
    db.create_all()
    #TOUR_database.__table__.drop(db.engine)
    #TOUR_PLAYERS_database.__table__.drop(db.engine)
    #app.run(ssl_context='adhoc')
    app.run()
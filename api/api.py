from flask import *
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from datetime import datetime, timedelta

app = Flask(__name__)

def get_db():
    cred = credentials.Certificate(os.getcwd().replace('\\','/') + '/myapp-e9807-firebase-adminsdk-qmrgn-b57c2d49e4.json')
    firebase_admin.initialize_app(cred)
    
    return firestore.client()

# Initialize our database
db = get_db()

def posts_collection():
    posts = db.collection('all_posts')    
    return [doc.to_dict() for doc in posts.stream()]

def users_collection():
    users = db.collection('usernames_list')
    return [doc.to_dict() for doc in users.stream()]

# Welcome page
@app.route('/')
def hello_page():
    return "Welcome on Diary's official API !"

# Get all users
@app.route('/users/')
def get_all_users():
    users = users_collection()
    dic = [item for item in users]
    return jsonify(dic)

# Get profile info from specific user
@app.route('/users/profile/<id>/')
def get_info_of_user(id):
    users = users_collection()
    dic = [item for item in users if item["userId"] == id]
    return jsonify(dic)

# Get all posts from specific user
@app.route('/users/posts/<id>/')
def get_posts_of_user(id):
    posts = posts_collection()
    dic = [item for item in posts if item["userId"] == id]
    return jsonify(dic)

# Get all posts
@app.route('/posts/')
def get_all_posts():
    posts = posts_collection()
    dic = [item for item in posts][::-1]
    return jsonify(dic)

# Get all posts in the last X days
@app.route('/posts/<days>/')
def get_posts_lastdays(days):
    posts = db.collection('all_posts')
    last_days = datetime.now() + timedelta(days=-int(days))
    query = posts \
        .where('timestamp', '>=', last_days) \
        .order_by('timestamp', 'DESCENDING')
    dic = [doc.to_dict() for doc in query.stream()]
    return jsonify(dic)

if __name__ == '__main__':
    app.run()
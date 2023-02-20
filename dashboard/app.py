from flask import *
from turbo_flask import Turbo
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
from datetime import datetime, timedelta
from collections import Counter
import itertools
import folium
from textblob import TextBlob

app = Flask(__name__)
app.debug = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
turbo = Turbo(app)

#############################

# Initialize our database
def get_db():
    cred = credentials.Certificate(os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\','/') + '/myapp-e9807-firebase-adminsdk-qmrgn-b57c2d49e4.json')
    firebase_admin.initialize_app(cred)
    
    return firestore.client()

db = get_db()

def posts_collection():
    posts = db.collection('all_posts')    
    return [doc.to_dict() for doc in posts.stream()]

def users_collection():
    users = db.collection('usernames_list')
    return [doc.to_dict() for doc in users.stream()]

def get_profile_by_id(id):
    users = users_collection()
    dic = [item for item in users if item["userId"] == id]
    return dic

# Dynamic values
total_users = 0
total_posts = 0
start_coords = (25.856021, 15.939946)
folium_map = folium.Map(location=start_coords, zoom_start=2, width=1034, height=620)
folium.TileLayer(tiles='https://tiles.stadiamaps.com/tiles/alidade_smooth_dark/{z}/{x}/{y}{r}.png', attr='&copy; <a href="https://stadiamaps.com/">Stadia Maps</a>, \
                 &copy; <a href="https://openmaptiles.org/">OpenMapTiles</a> &copy; <a href="http://openstreetmap.org">OpenStreetMap</a> contributors').add_to(folium_map)

total_likes = 0
total_images = 0
leaderboard = []

def get_most_active_users():
    global leaderboard
    posts = posts_collection()
    occurences = list(itertools.chain(*[doc['liked_by'] for doc in posts])) + [doc['userId'] for doc in posts]
    counts = sorted(Counter(occurences).items(), key=lambda x: (-x[1], x[0]))
    counts = [(get_profile_by_id(e[0])[0]['username'],e[1],get_profile_by_id(e[0])[0]['profileurl'],e[0]) for e in counts][:3]
    leaderboard = counts

def parse_position(position):
    try:
        latitude = position.split(',')[0].split(': ')[1]
        longitude = position.split(',')[1].split(': ')[-1]
        
        return latitude,longitude
    except BaseException:
        return None,None


# Snapshot functions
def on_snapshot_users(col_snapshot, changes, read_time):
    for change in changes:
        global total_users
        if change.type.name == "ADDED":
            total_users += 1
        elif change.type.name == 'REMOVED':
            total_users -= 1
    turbo.push(turbo.replace(f'<div id= "total-users" class="number">{total_users}</div>', 'total-users'))
  
def on_snapshot_posts(col_snapshot, changes, read_time):
    for change in changes:
        global total_posts
        global total_likes
        global total_images
        global folium_map
        if change.type.name == "ADDED":
            total_likes = 0
            total_images = 0
            total_posts += 1
            for item in col_snapshot:
                total_likes += item.to_dict()['likes']
                if len(item.to_dict()['imageUrl']) > 1:
                    total_images += 1
                latitude, longitude = parse_position(item.to_dict()['position'])
                if latitude == None:
                    continue
                username = item.to_dict()['username']
                text = item.to_dict()['text'].replace('`', '')
                sentiment = TextBlob(text).sentiment.polarity
                timestamp = str(item.to_dict()['timestamp']).split('.')[0].split('+')[0]
                if sentiment < 0:
                    folium.Circle(location=[latitude,longitude], popup= folium.Popup("<b>Username: </b>"+username+"<br>"+"<b>Post: </b>"+text+"<br>"+"<b>Sentiment: </b>"+"Negative"+"<br>"+\
                        "<b>Timestamp: </b>"+timestamp,max_width=200), color='red', fill=True, fill_color = 'red').add_to(folium_map)
                elif sentiment == 0:
                    folium.Circle(location=[latitude,longitude], popup= folium.Popup("<b>Username: </b>"+username+"<br>"+"<b>Post: </b>"+text+"<br>"+"<b>Sentiment: </b>"+"Neutral"+"<br>"+\
                        "<b>Timestamp: </b>"+timestamp,max_width=200), color='blue', fill=True, fill_color = 'blue').add_to(folium_map)
                else:
                    folium.Circle(location=[latitude,longitude], popup= folium.Popup("<b>Username: </b>"+username+"<br>"+"<b>Post: </b>"+text+"<br>"+"<b>Sentiment: </b>"+"Positive"+"<br>"+\
                        "<b>Timestamp: </b>"+timestamp,max_width=200), color='green', fill=True, fill_color = 'green').add_to(folium_map)
        elif change.type.name == 'REMOVED':
            total_posts -= 1
    turbo.push(turbo.replace(f'<div id= "total-posts" class="number">{total_posts}</div>', 'total-posts'))
    turbo.push(turbo.replace(f'<div id= "total-likes" class="number">{total_likes}</div>', 'total-likes'))
    turbo.push(turbo.replace(f'<div id= "total-images" class="number">{total_images}</div>', 'total-images'))
    if len(changes) == 1 and changes[0].type.name != 'REMOVED' and changes[0].type.name != 'MODIFIED':
        turbo.push(turbo.replace('<iframe id="world-map" src="/map" name="targetframe" allowTransparency="true" scrolling="no" frameborder="0" width="1050" height="650"></iframe>', 'world-map'))
    

col_ref_users = db.collection(u'usernames_list')
col_ref_posts = db.collection(u'all_posts')

col_ref_users.on_snapshot(on_snapshot_users)
col_ref_posts.on_snapshot(on_snapshot_posts)

###################

# Inject updated values
@app.context_processor
def inject_load():
    return {'total_users': total_users, 'total_posts': total_posts, 'total_likes': total_likes, 'total_images':total_images}

# Home page
@app.route('/')
def hello_page():
    get_most_active_users()
    posts = db.collection('all_posts').stream()
    all_dates = [(str(post.id)[:10]) for post in posts]
    values = [[date,all_dates.count(date)][1] for date in sorted(set(all_dates))]
    return render_template('index.html', leaderboard=leaderboard, labels=sorted(set(all_dates)), values=values)

@app.route('/map/')
def map():
    global folium_map
    return render_template_string(folium_map._repr_html_())

@app.route('/api/v1/')
def api_home():
    return render_template('api.html')

# Get all users
@app.route('/api/v1/users/')
def get_all_users():
    users = users_collection()
    dic = [item for item in users]
    return jsonify(dic)

# Get profile info from specific user
@app.route('/api/v1/users/profile/<id>/')
def get_info_of_user(id):
    users = users_collection()
    dic = [item for item in users if item["userId"] == id]
    return jsonify(dic)

# Get all posts from specific user
@app.route('/api/v1/users/posts/<id>/')
def get_posts_of_user(id):
    posts = posts_collection()
    dic = [item for item in posts if item["userId"] == id]
    return jsonify(dic)

# Get all posts
@app.route('/api/v1/posts/')
def get_all_posts():
    posts = posts_collection()
    dic = [item for item in posts][::-1]
    return jsonify(dic)

# Get all posts in the last X days
@app.route('/api/v1/posts/<days>/')
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
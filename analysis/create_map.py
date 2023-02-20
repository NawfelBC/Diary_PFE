import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
import folium
from NLP import get_score
from transformers import logging
logging.set_verbosity_error()
    
def get_db():
    cred = credentials.Certificate(os.path.dirname(os.path.dirname(__file__)).replace('\\','/') + '/myapp-e9807-firebase-adminsdk-qmrgn-b57c2d49e4.json')
    firebase_admin.initialize_app(cred, {'storageBucket': 'myapp-e9807.appspot.com'})
    
    return firestore.client()

def upload_map_to_db(map):
    fileName = "map.html"
    bucket = storage.bucket()
    blob = bucket.blob(fileName)
    blob.upload_from_string(map, content_type='text/html')
    blob.make_public()

def parse_position(position):
    latitude = position.split(',')[0].split(': ')[1]
    longitude = position.split(',')[1].split(': ')[-1]
    
    return latitude,longitude

def generate_map(items):
    map = folium.Map(location=[25.856021, 15.939946], zoom_start=2)
    folium.TileLayer('cartodbdark_matter').add_to(map)
    i = 1
    for item in items:
        if item.to_dict()['position'] == "null":
            continue
        print(f'Creating item {i}..')
        i += 1
        lat,lng = parse_position(item.to_dict()['position'])
        username = item.to_dict()['username']
        text = item.to_dict()['text'].replace('`', '')
        sentiment = get_score(text)
        timestamp = str(item.to_dict()['timestamp']).split('.')[0].split('+')[0]

        if sentiment == 0:
            folium.Circle(location=[lat,lng] , popup= folium.Popup("<b>Username: </b>"+username+"<br>"+"<b>Post: </b>"+text+"<br>"+"<b>Sentiment: </b>"+"Negative"+"<br>"+\
                "<b>Timestamp: </b>"+timestamp,max_width=200),color='red', fill=True, fill_color = 'red').add_to(map)
        elif sentiment == 1:
            folium.Circle(location=[lat,lng] , popup= folium.Popup("<b>Username: </b>"+username+"<br>"+"<b>Post: </b>"+text+"<br>"+"<b>Sentiment: </b>"+"Neutral"+"<br>"+\
                "<b>Timestamp: </b>"+timestamp,max_width=200),color='blue', fill=True, fill_color = 'blue').add_to(map)
        elif sentiment == 2:
            folium.Circle(location=[lat,lng] , popup= folium.Popup("<b>Username: </b>"+username+"<br>"+"<b>Post: </b>"+text+"<br>"+"<b>Sentiment: </b>"+"Positive"+"<br>"+\
                "<b>Timestamp: </b>"+timestamp,max_width=200),color='green', fill=True, fill_color = 'green').add_to(map)
            
    print('Map successfully generated !')
    return map.get_root().render()

if __name__ == '__main__':
    posts = get_db().collection('all_posts').stream()
    map = generate_map(posts)
    upload_map_to_db(map)
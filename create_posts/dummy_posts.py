import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import random
import pandas as pd
from faker import Faker
import ciso8601

def get_db():
    cred = credentials.Certificate(os.path.dirname(os.getcwd()).replace('\\','/') + '/myapp-e9807-firebase-adminsdk-qmrgn-b57c2d49e4.json')
    firebase_admin.initialize_app(cred)
    
    return firestore.client()

def get_random_user(db):
    users = db.collection('usernames_list').stream()
    items = [user.to_dict() for user in users]
    random_idx = random.randint(0,len(items)-1)
    random_user = items[random_idx]
    
    return random_user

def get_random_timestamp():
    return Faker().date_time_between(start_date='-1y', end_date='now').strftime('%Y-%m-%d %H:%M:%S.%f')

def get_random_position():
    filename = os.getcwd().replace('\\','/') + '/worldcities.csv'
    file = pd.read_csv(filename)
    sample = file.sample()
    lat = float(sample['lat'])
    lng = float(sample['lng'])
    
    return f"Latitude: {lat}, Longitude: {lng}"

def get_random_text():
    filename = os.getcwd().replace('\\','/') + '/tweets.csv'
    file = pd.read_csv(filename)
    sample = file.sample().values[0][1]

    return str(sample).strip()

def new_post(db):
    user = get_random_user(db)
    timestamp = get_random_timestamp()
    print(timestamp)
    doc_id = str(timestamp) + user['userId']
    position = get_random_position()
    print(position)
    data = {'edited':'N', 
            'imageUrl':'', 
            'liked_by':[], 
            'likes':0, 
            'position':position, 
            'profileurl':user['profileurl'], 
            'text':get_random_text(), 
            'timestamp':ciso8601.parse_datetime(timestamp), 
            'userId':user['userId'], 
            'username':user['username']}

    with open('dummy_posts_ids.txt', 'a') as f: 
        f.write(doc_id+'\n')
    
    db.collection('all_posts').document(doc_id).set(data)
    # db.collection(user['userId']).document(doc_id).set(data)

if __name__ == '__main__':
    db = get_db()
    # for i in range(50):
    #     print(f'Creating post {i}')
    new_post(db)
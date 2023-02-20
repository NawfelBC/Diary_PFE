import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import pandas as pd

cred = credentials.Certificate(os.path.dirname(os.getcwd()).replace('\\','/') + '/myapp-e9807-firebase-adminsdk-qmrgn-b57c2d49e4.json')
firebase_admin.initialize_app(cred)

db = firestore.client()

posts = db.collection('all_posts').stream()

all_dates = [(str(post.to_dict()['timestamp'])[:10]) for post in posts]

lst = [[date,all_dates.count(date)] for date in set(all_dates)]

df = pd.DataFrame(lst, columns=['Date', 'Evolution of number of posts'])
df.set_index(['Date'],inplace=True)
plot = df.plot(title="test")
fig = plot.get_figure()
fig.savefig("evolution_of_posts.png")
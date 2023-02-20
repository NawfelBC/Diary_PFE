from flask import Flask
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import openai
import os

app = Flask(__name__)

OPENAI_TOKEN = os.environ.get("OPENAI_TOKEN")
openai.api_key = OPENAI_TOKEN
chatbot = openai.Completion()
dalle = openai.Image()

@app.route('/')
def home():
    return "I'm alive"

def get_db():
    cred = credentials.Certificate(os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\','/') + '/myapp-e9807-firebase-adminsdk-qmrgn-b57c2d49e4.json')    
    firebase_admin.initialize_app(cred)
    
    return firestore.client()

def on_snapshot_posts(col_snapshot, changes, read_time):
    for change in changes:
        if change.type.name == "ADDED":
            for item in col_snapshot:
                documentId = item.id
                userId = item.to_dict()['userId']
                text = item.to_dict()['text'].replace('`', '')
                if '/image' in text.lower() and '/chatgpt' not in text.lower() and item.to_dict()['imageUrl'] == "":
                    prompt = text.lower().replace('/image ','')
                    db.collection('all_posts').document(documentId).update({'text': f'Generating image.. (prompt: {prompt})'})
                    db.collection(userId).document(documentId).update({'text': f'Generating image.. (prompt: {prompt})'})
                    try:
                        response = dalle.create(prompt=prompt, n=1)
                        image_url = response['data'][0]['url']     
                        db.collection('all_posts').document(documentId).update({'text': prompt, 'imageUrl': image_url})
                        db.collection(userId).document(documentId).update({'text': prompt, 'imageUrl': image_url})
                    except BaseException as e:
                        print(e)
                        continue
                elif '/chatgpt' in text.lower() and '/image' not in text.lower():
                    chatgpt_input = text.lower().replace('/chatgpt ','')
                    db.collection('all_posts').document(documentId).update({'text': f'Generating text.. (prompt: {chatgpt_input})'})
                    db.collection(userId).document(documentId).update({'text': f'Generating text.. (prompt: {chatgpt_input})'})
                    try:
                        response = chatbot.create(engine="text-davinci-003", prompt=chatgpt_input, max_tokens=1000, temperature=0.5)
                        chatgpt_output = str(response.choices[0].text).strip()
                        db.collection('all_posts').document(documentId).update({'text': chatgpt_output})
                        db.collection(userId).document(documentId).update({'text': chatgpt_output})
                    except BaseException as e:
                        print(e)

db = get_db()
col_ref_posts = db.collection(u'all_posts')
col_ref_posts.on_snapshot(on_snapshot_posts)

if __name__ == "__main__":
    app.run('0.0.0.0', port=8080)

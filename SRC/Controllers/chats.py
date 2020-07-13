from src.app import app
from pymongo import MongoClient
from src.Helpers.errorHelpers import errorHelper ,Error404 ,APIError
from src.config import DBURL
from bson.json_util import dumps
from flask import request
from datetime import datetime
from bson import ObjectId
import requests
import ast
import re
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from classifier import *
clf = SentimentClassifier()


#DBURL='mongodb://192.168.1.73:27017/'
client = MongoClient(DBURL)
db = client.get_database("dbChat")

## L1 USER ENDPOINTS
@app.route("/user/create/<username>")
@errorHelper
def insertUser(username):
    if username:
        dic={
            'user_name':username,
            'insertion_date':getDate(),
            'chats_list': []
        }
        user_id=db.users.insert_one(dic)
    else:
        print("ERROR")
        raise Error404("name not found")
    return json.dumps({'user_id':str(user_id.inserted_id)})



'''- (GET) `/chat/create`
  - **Purpose:** Create a conversation to load messages
  - **Params:** An array of users ids `[user_id]`
  - **Returns:** `chat_id`''' 
  
@app.route("/chat/create") #?ids=<arr>&name=<chatname>
@errorHelper
def insertChat():
    arr = request.args.get("ids")
    print(arr)
    name= request.args.get("name",default='')
    
    #creation of a new chat with the users included in arr
    if arr:
        arr=ast.literal_eval(arr)
        dic={   
            'chat_name': name,
            'creation_date':getDate(),
            'users_list':[],
            'messages_list':[]
        }
        chat_id=db.chats.insert_one(dic)
        #insert the users in the chat
        chatId=chat_id.inserted_id
        for user_id in arr:
            #r = requests.get(f'http://localhost:3500/chat/{chatId}/adduser?user_id={user_id}')
            r=addChatUser(chatId, user_id)
        #update of the users chats_list by adding the chat id
        for user_id in arr:
            post=db.users.find_one({'_id':ObjectId(user_id)})
            post['chats_list'].append(ObjectId(chat_id.inserted_id))
            db.users.update_one({'_id':ObjectId(user_id)}, {"$set": post}, upsert=False)

    else:
        print("ERROR")
        raise APIError("Tienes que mandar un query parameter ?ids=<arr>&name=<chatname>")
    
    return json.dumps({'chat_id':str(chat_id.inserted_id)})



'''- (GET) `/chat/<chat_id>/adduser`
  - **Purpose:** Add a user to a chat, this is optional just in case you want to add more users to a chat after it's creation.
  - **Params:** `user_id`
  - **Returns:** `chat_id`'''

@app.route("/chat/<chat_id>/adduser") #?user_id=<user_id>
@errorHelper
def addChatUser(chat_id, user_id=None):
    if user_id==None:
        user_id= request.args.get("user_id")
    if user_id!=None and chat_id!=None:
        #update of the chat document by adding the user id
        post=db.chats.find_one({'_id':ObjectId(chat_id)})
        if ObjectId(user_id) not in post['users_list']:
            post['users_list'].append(ObjectId(user_id))
        db.chats.update_one({'_id':ObjectId(chat_id)}, {"$set": post}, upsert=False)
        
        #update of the user permissions by adding the chat id
        post=db.users.find_one({'_id':ObjectId(user_id)})
        if ObjectId(chat_id) not in post['chats_list']:
            post['chats_list'].append(ObjectId(chat_id))
        db.users.update_one({'_id':ObjectId(user_id)}, {"$set": post}, upsert=False)
    elif not chat_id:
        print("ERROR")
        raise Error404("chat_id not found")
    elif not user_id:
        print("ERROR")
        raise APIError("You should send these query parameters ?user_id=<user_id>")

    return json.dumps({'chat_id': str(chat_id)})



'''(POST) `/chat/<chat_id>/addmessage`
  - **Purpose:** Add a message to the conversation. 
  Help: Before adding the chat message to the database, 
  check that the incoming user is part of this chat id. If not, raise an exception.
  - **Params:**
    - `chat_id`: Chat to store message
    - `user_id`: the user that writes the message
    - `text`: Message text
  - **Returns:** `message_id`
    '''

@app.route("/chat/<chat_id>/addmessage") #?user_id=<user_id>&text=<text>
@errorHelper
def addMessage(chat_id):
    user_id= request.args.get("user_id")
    text= request.args.get("text")
    
    #check if the user has the permission to post in the chat or raise an exception
    get=db.chats.find_one({"_id":ObjectId(chat_id) })
    if not ObjectId(user_id) in get['users_list']:
        raise PermissionError("Permission denied")

    #add the message to the messages collection and get the id
    
    dic={
         'user_id': ObjectId(user_id),
         'text':text,
         'time':getDate(),
         'chat_id':ObjectId(chat_id)
    }
    message_id=db.messages.insert_one(dic)
    
    #add the message text to the messages_list of the chat

    post=db.chats.find_one({"_id":ObjectId(chat_id)})
    post['messages_list'].append(message_id.inserted_id)
    db.chats.update_one({'_id':ObjectId(chat_id)}, {"$set": post}, upsert=False)
    
    return json.dumps({'message_id':str(message_id.inserted_id)})


'''- (GET) `/chat/<chat_id>/list`
- **Purpose:** Get all messages from `chat_id`
- **Returns:** json array with all messages from this `chat_id`'''

@app.route("/chat/<chat_id>/list") 
@errorHelper
def getMessages(chat_id):
    #try:
    get=db.chats.find_one({"_id":ObjectId(chat_id)})
    messages_ids=[]
    for el in get['messages_list']:
        messages_ids.append(str(el))
    diz={}
    for m in messages_ids:
        r=db.messages.find_one({'_id':ObjectId(m)})
        diz[m]=r['text']
    #except:
    #   raise APIError("chat id not found")
    return json.dumps(diz)

'''- (GET) `/chat/<chat_id>/sentiment`
  - **Purpose:** Analyze messages from `chat_id`. Use `NLTK` sentiment analysis package for this task
  - **Returns:** json with all sentiments from messages in the chat
'''
nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()
@app.route("/chat/<chat_id>/sentiment") #?lang=<lang>
@errorHelper
def getSentiment(chat_id):  
    #mess=requests.get(f'http://localhost:3500/chat/{chat_id}/list').json()
    mess=ast.literal_eval(getMessages(chat_id))
    sentiments={}
    try:
        lang= request.args.get("lang")
    except:
        raise APIError("You should specify the language of the chat in the query parameters [english='en',spanish='es'] ?lang=<lang>")

    if lang=='en':

        for id, text in mess.items():
            sentiments[id]={'text':text,"score":sia.polarity_scores(text)} 
        sums=0
        for v in sentiments.values():
            sums+=v['score']['compound']
        avg=sums/len(sentiments)
        sentiments['chat_sentiment']=avg
    else:
        for id, text in mess.items():
            sentiments[id]={'text':text,"score":clf.predict(text)} 
        sums=0
        for v in sentiments.values():
            sums+=v['score']*2-1#normalize the score(in senti the score_value domain is [0,1])
        avg=sums/len(sentiments)
        sentiments['chat_sentiment']=avg

    return json.dumps(sentiments)



'''- (GET) `/chat/ids`
- **Purpose:** Get all chat_id from the collection `chats`
- **Returns:** json dict with all `chat_id` in the database'''

@app.route("/chat/ids") 
@errorHelper
def getChatIds():
    #try:
    chat_ids={}
    get=list(db.chats.find({},{'_id':1}))
    for diz in get:      
        for k,v in diz.items():
            chat_ids[str(v)]=str(v)
    #except:
    #   raise APIError("chat id not found")
    return json.dumps(chat_ids)

def getDate():
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")
    return dt_string
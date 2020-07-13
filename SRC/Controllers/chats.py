from src.app import app
from pymongo import MongoClient
from src.Helpers.errorHelpers import errorHelper ,Error404 ,APIError
from src.config import DBURL
from bson.json_util import dumps
from flask import request
from bson import ObjectId
import requests
import re
import json
import nltk
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
# from classifier import *
#clf = SentimentClassifier()

client = MongoClient(DBURL, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000)
db = client.get_database()

@app.route("/")
def begin():
     return "Welcome to my API! Feel free to start creating convos and adding users to them! :)"

## L1 USER ENDPOINTS
@app.route("/user/create/<username>")
@errorHelper
def createUser(username):
    """
        Create a user that will be part of conversations in the future.
    """
    if username:
        dic={
            'user_name':username,
            'chats': []
        }
        user_id=db.users.insert_one(dic)
    else:
        print("ERROR")
        raise Error404("name not found")
    return f"Congrats! You just created a user called {username} with user_id: {user_id}"



# Chat endpoint 1: 
@app.route("/chat/create")
@errorHelper
def createChat():
    """
        Create a conversation to load messages on it.
    """
    arr = request.args.get("ids")
    name = request.args.get("name")
    
    #creation of a new chat with the users included in arr
    if arr:
        dic={   
            'chat_name': name,
            'users_list':[],
            'messages_list':[]
        }
        
        chat_id=db.chats.insert_one(dic)
        chatID = chat_id.inserted_id
        for user_id in arr:
            addUser(chatID, user_id)
            user = db.users.find_one({'_id':ObjectId(user_id)})
            user['chats'].append(ObjectId(chat_id.inserted_id))

    else:
        print("ERROR")
        raise APIError("You have to send a query parameter as ?ids=<arr>")
    
    return {'chat_id':str(chat_id.inserted_id)}



@app.route("/chat/<chat_id>/adduser") #?user_id=<user_id>
@errorHelper
def addUser(chat_id, user_id):
    user_id= request.args.get("user_id")
    if not chat_id:
        print("ERROR")
        raise Error404("chat_id not found")
    elif not user_id:
        print("ERROR")
        raise APIError("You should send these query parameters ?user_id=<user_id>")
    elif user_id!=None and chat_id!=None:
        # This updates the users collection so that each user has a list with all the groups he is in
        users=db.users.find_one({'_id':ObjectId(user_id)})
        if ObjectId(chat_id) not in users['chats']:
            users['chats'].append(ObjectId(chat_id))
        #update of the chat document by adding the user id
        chat=db.chats.find_one({'_id':ObjectId(chat_id)})
        if ObjectId(user_id) not in chat['users_list']:
            chat['users_list'].append(ObjectId(user_id))
        
    return {'chat_id': str(chat_id)}



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
         'chat_id':ObjectId(chat_id)
    }
    message_id=db.messages.insert_one(dic)
    
    #add the message text to the messages_list of the chat

    post=db.chats.find_one({"_id":ObjectId(chat_id)})
    post['messages_list'].append(message_id.inserted_id)
    db.chats.update_one({'_id':ObjectId(chat_id)}, {"$set": post}, upsert=False)
    
    return json.dumps({'message_id':str(message_id.inserted_id)})


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



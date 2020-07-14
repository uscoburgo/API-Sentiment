from src.app import app
from pymongo import MongoClient
from src.Helpers.errorHelpers import errorHelper ,Error404 ,APIError
from src.config import DBURL
from flask import request
from bson import ObjectId
import requests
import re
import json
import nltk
import ast
from nltk.sentiment.vader import SentimentIntensityAnalyzer
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
        raise Error404("No name input")
    return {'user_id':str(user_id.inserted_id)}



# Chat endpoint 1: 
  
@app.route("/chat/create") #?ids=<arr>&name=<chatname>
@errorHelper
def createChat():
    list_users = request.args.getlist("ids")
    conversation_name = request.args.get("name")
    
    #creation of a new chat with the users included in arr
    if list_users:
        dic={'chat_name': conversation_name,'users_list':[],'messages_list':[]}
        chat = db.chats.insert_one(dic)

        chatId = str(chat.inserted_id)
    
        for user_id in list_users:
            #insert the users in the chat
            db.chats.update_one({'_id':ObjectId(chatId)}, {"$push": {"users_list": ObjectId(user_id)}})
            #update of the users chats_list by adding the chat id
            db.users.update_one({'_id':ObjectId(user_id)}, {"$push": {"chats": ObjectId(chatId)}})

    else:
        print("ERROR")
        raise APIError("Tienes que mandar un query parameter ?ids=<arr>&name=<chatname>")
    
    return {f'Congrats, you just created a chat called {conversation_name} with chat_id':str(chat.inserted_id)}



@app.route("/chat/<chat_id>/adduser")
@errorHelper
def addUser(chat_id):
    user = request.args.get("user_id")
    if not chat_id:
        print("ERROR")
        raise Error404("The chat id wasn't entered")
    if not user:
        print("ERROR")
        raise APIError("The user wasn't entered")
    else:
        #insert the users in the chat
        db.chats.update_one({'_id':ObjectId(chat_id)}, {"$push": {"users_list": ObjectId(user)}})
        #update of the users chats_list by adding the chat id
        db.users.update_one({'_id':ObjectId(user)}, {"$push": {"chats": ObjectId(chat_id)}})

    return {f'we just entered user: {user} to chat_id: {str(chat_id)}'}


@app.route("/chat/<chat_id>/addmessage") #?user_id=<user_id>&text=<text>
@errorHelper
def addMessage(chat_id):
    user_id= request.args.get("user_id")
    text= request.args.get("text")
    
    #check if the user has the permission to post in the chat or raise an exception
    chat=db.chats.find_one({"_id":ObjectId(chat_id) })
    if not ObjectId(user_id) in chat['users_list']:
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
    
    return {'message_id':str(message_id.inserted_id)}


@app.route("/chat/<chat_id>/list") 
@errorHelper
def getMessage(chat_id):
    get=db.chats.find_one({"_id":ObjectId(chat_id)})
    messages_ids=[]
    for el in get['messages_list']:
        messages_ids.append(str(el))
    diz={}
    for m in messages_ids:
        r = db.messages.find_one({'_id':ObjectId(m)})
        diz[m]=r['text']

    return diz

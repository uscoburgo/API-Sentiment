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
        dic={
            'chat_name': conversation_name,
            'users':[],
            'messages':[]
        }
        chat = db.chats.insert_one(dic)

        chatId = str(chat.inserted_id)
    
        for user_id in list_users:
            #insert the users in the chat
            db.chats.update_one({'_id':ObjectId(chatId)}, {"$push": {"users": ObjectId(user_id)}})
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
    else:
        #insert the users in the chat
        db.chats.update_one({'_id':ObjectId(str(chat_id))}, {"$push": {"users": ObjectId(str(user))}})
        #update of the users chats_list by adding the chat id
        db.users.update_one({'_id':ObjectId(str(user))}, {"$push": {"chats": ObjectId(str(chat_id))}})

    return {'entered user': {user}, 
            'chat_id': {str(chat_id)}
        }


@app.route("/chat/<chat_id>/addmessage") 
@errorHelper
def addMessage(chat_id):
    user = request.args.get("user_id")
    message = request.args.get("text")
    
    # Making sure that the user is in the group
    chat=db.chats.find_one({"_id":ObjectId(chat_id) })
    if not ObjectId(user) in chat['users']:
        raise Error404("User is not a member of the chat")

    #add the message to the messages collection and get the id
    dic={
         'user': ObjectId(user),
         'message':message,
         'chat_id':ObjectId(chat_id)
    }
    messageID = db.messages.insert_one(dic)
    #add the message text to the messages of the chat
    db.chats.update_one({'_id':ObjectId(chat_id)}, {"$push": {"messages": messageID.inserted_id}})  

    return f'We just entered message: {message} to chat_id: {str(chat_id)}'



@app.route("/chat/<chat_id>/list") 
@errorHelper
def getMessage(chat_id):
    chat=db.chats.find_one({"_id":ObjectId(chat_id)})
    messagesID=[]
    dict_messages={}
    for ID in chat['messages']:
        messagesID.append(str(ID))
    
    for m in messagesID:
        r = db.messages.find_one({'_id':ObjectId(m)})
        dict_messages[m]=r['message']

    return dict_messages

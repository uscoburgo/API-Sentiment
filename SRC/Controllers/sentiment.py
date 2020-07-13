from src.Controllers.chats import getMessages
from src.app import app
from pymongo import MongoClient
from src.Helpers.errorHelpers import errorHelper ,Error404 ,APIError
from bson.json_util import dumps
from flask import request
from bson import ObjectId
import requests
import re
import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()
@app.route("/chat/<chat_id>/sentiment") #?user_id=<user_id>
@errorHelper
def getSentiment(chat_id):  
    sentiments={}

    for id, text in getMessages(chat_id):
        sentiments[id]={'text':text,"score":sia.polarity_scores(text)} 
    sums=0
    for v in sentiments.values():
        sums+=v['score']['compound']
    avg=sums/len(sentiments)
    sentiments['chat_sentiment']=avg

    return sentiments
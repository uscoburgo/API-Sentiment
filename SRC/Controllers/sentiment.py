from src.Controllers.chats import getMessage
from src.app import app
from pymongo import MongoClient
from src.Helpers.errorHelpers import errorHelper ,Error404 ,APIError
from src.config import DBURL
import json
import nltk
import ast
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity as distance
import pandas as pd
from bson import ObjectId

client = MongoClient(DBURL, connectTimeoutMS=2000, serverSelectionTimeoutMS=2000)
db = client.get_database()

nltk.download("vader_lexicon")
sia = SentimentIntensityAnalyzer()
@app.route("/chat/<chat_id>/sentiment") #?lang=<lang>
@errorHelper
def getSentiment(chat_id):  
    sentimentMessage={}
    for ID, message in getMessage(chat_id).items():
        sentimentMessage[ID]={"message":message,"sentiment":sia.polarity_scores(message)} 
    sums=0
    for v in sentimentMessage.values():
        print(v)
        sums+=v['sentiment']['compound']
    average = sums/len(sentimentMessage)
    sentimentMessage['overall sentiment']=average

    return sentimentMessage

"""
    @app.route("/user/<user_id>/recommend")
@errorHelper
def getRecommendation(user_id):
    stringsDict = {}  
    cur = db.messages.find({},{'_id':0,'user_id':1,'text':1})
    data = list(cur)
    for e in len(data):
        stringsDict.update({data[e]['user_id'] : data[e]['text']})
    
    sent1 = {}#k =user_id, v=text
    for k,v in stringsDict.items():    
        sent1[k]=str(v)
    
    count_vectorizer = CountVectorizer()
    sparse_matrix = count_vectorizer.fit_transform(sent1.values())
    doc_term_matrix = sparse_matrix.todense()
    df = pd.DataFrame(doc_term_matrix, 
                  columns=count_vectorizer.get_feature_names(), 
                  index=sent1.keys())
    similarity_matrix = distance(df,df)
    sim_df = pd.DataFrame(similarity_matrix, columns=sent1.keys(), index=sent1.keys())
    def get3closest(sim_df,user_id):#user is an ObjectId
        col=sim_df[user_id].sort_values(ascending=False)[1:]
        return list(col[0:3].index)
    output= get3closest(sim_df,ObjectId(user_id))
    output=[str(el) for el in output]
    return {'recommended':output}
    """
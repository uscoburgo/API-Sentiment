# API-Sentiment

<img src="INPUT/conversation.jpg">

## Overview

The goal of this project was creating an API containing messages and using sentiment analysis and NLP to group similar users together.

[x] L1 - Write an API in `flask` just to store chat messages in a mongodb database.
[x] L2(A) - Extract sentiment from chat messages and perform a report over a whole conversation
[ ] L2(B) - Recommend friends to a user based on the contents from chat `documents` using a recommender system with `NLP` analysis.
[x] L3 - Deploy the service with docker to heroku and store messages in a cloud database.
[ ] L4 - **HOT** Do it real, use slack API to get messages and analyze the messages of our `datamad` channel.

The project is divided into numerous files:
- L1 takes place in chats.py
- L2 takes place in sentiment.py
- L3 takes place in Dockerfile

## Flask commands

### L1 checkpoints

- To create a user you will have to do: `/user/create/<username>`
- To create a chat with users you will have to type in: `/chat/create?ids=<arr>&name=<chatname>`
- To add a user to a chat you will have to do: `/chat/<chat_id>/adduser?user_id=<user_id>`
- To add a message to a chat, you will have to do: `/chat/<chat_id>/addmessage?user_id=<user_id>&text=<text>`
- To get a list of all messages for a chat_id you'll have to do: `/chat/<chat_id>/list`

### L2 checkpoints
- To get the sentiment of messages you'll have to do: `/chat/<chat_id>/sentiment`

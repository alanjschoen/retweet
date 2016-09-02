'''Initialize tweetsat database for each user'''

# Set up twitter access
# pip install tweepy
import cnfg
import tweepy
config = cnfg.load(".twitter_config")
auth = tweepy.OAuthHandler(config["consumer_key"],
                           config["consumer_secret"])
auth.set_access_token(config["access_token"],
                      config["access_token_secret"])
api=tweepy.API(auth)

# Set up database
from pymongo import MongoClient
client = MongoClient()
db = client.retweets

# Set max tweets for initialization and update
max_tweets_init=5000

accounts = ['@donlemon', '@kanyewest', '@realDonaldTrump', '@JusticeWillett', '@IAmSteveHarvey', '@juliaioffe',
            '@ForecasterEnten', '@pmarca']

# Clear db if it exists
for username in accounts:
    collection_name = username + '_tweets'
    if collection_name in db.collection_names():
        print "Found collection %s.  Deleting..."%collection_name
        db[collection_name].drop()

# Initialize for each user
from harvester import TwitterUser
for username in accounts:
    user = TwitterUser(username, api, db)
    user.update_tweetsat(max_tweets_init)
print 'Done updating'


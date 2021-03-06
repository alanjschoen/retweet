'''Classes and functions for dowloading tweets and retweets'''

import tweepy
import time

# Retweet class has methods to collect and store information about a retweet
# Tweet must be a dictionary.  Status objects should be converted with ._json
class Retweet:
    def __init__(self, tweet):
        tweet = tweet
        if 'quoted_status' in tweet:
            self.tweeter = '@' + tweet['quoted_status']['user']['screen_name']
            self.retweeter = '@' + tweet['user']['screen_name']
        else:
            self.tweeter = '@' + tweet['retweeted_status']['user']['screen_name']
            self.retweeter = '@' + tweet['user']['screen_name']
        self.retweet = tweet
    def get_history(self, api, ntweets):
        cursor = tweepy.Cursor(api.user_timeline,screen_name=self.tweeter, count=100).items(ntweets)
        self.tweeter_history = [tweet._json for tweet in limit_cursor(cursor)]
    def get_friendship(self, api):
        friendship = friendship_limited(api, self.tweeter, self.retweeter)
        self.follows1 = friendship[0].following
        self.follows2 = friendship[0].followed_by
    def save(self, db):
        collection_name = self.retweeter[1:] + '_retweets'
        target_colection = db[collection_name]
        target_colection.insert_one(self.__dict__)


# TwitterUser class has methods to read and store the activity of a twitter user
class TwitterUser:
    def __init__(self, screen_name, api, db):
        self.screen_name = screen_name
        self.db = db
        self.api = api
        self.check_tweetsat()
        self.check_tweets()

    def check_tweetsat(self):
        collection_name = self.screen_name[1:] + '_tweetsat'
        self.last_tweetsat = get_db_last(self.db, collection_name)

    def check_tweets(self):
        collection_name = self.screen_name[1:] + '_tweets'
        self.last_tweets = get_db_last(self.db, collection_name)

    def update_tweetsat(self, max_tweets, since_id=None):
        collection_name = self.screen_name[1:] + '_tweetsat'
        cursor = tweepy.Cursor(self.api.search, q=self.screen_name, count=300, since_id=self.last_tweetsat).items(max_tweets)
        count = store_tweets(cursor, self.db, collection_name)
        self.check_tweetsat()
        print "stored %d tweets at %s" % (count, self.screen_name)

    def update_tweets(self, max_tweets, since_id=None):
        collection_name = self.screen_name[1:] + '_tweets'
        cursor = tweepy.Cursor(self.api.user_timeline, screen_name=self.screen_name, count=300, since_id=self.last_tweets).items(
            max_tweets)
        count = store_tweets(cursor, self.db, collection_name)
        self.check_tweets()
        print "stored %d of %s's tweets" % (count, self.screen_name)

    def extend_tweets(self, nitems):
        collection_name = self.screen_name[1:] + '_tweets'
        first_tweet=get_db_first(self.db, collection_name)
        cursor = tweepy.Cursor(self.api.user_timeline, screen_name=self.screen_name, count=300,
                               max_id=first_tweet-1).items(nitems)
        count = store_tweets(cursor, self.db, collection_name)
        self.check_tweets()
        print "stored %d of %s's tweets" % (count, self.screen_name)


# Helper Functions:

# Enforce api limit on friendship
def friendship_limited(api, tweeter, retweeter):
    while True:
        try:
            return api.show_friendship(source_screen_name=tweeter, target_screen_name=retweeter)
        except tweepy.RateLimitError:
            print "Rate limited on friendship.  Waiting 5 mins."
            time.sleep(5 * 60)

# Enforce api limit on cursors
def limit_cursor(cursor):
    while True:
        try:
            yield cursor.next()
        except tweepy.RateLimitError as e:
            print e
            print "Rate limited on cursor.  Waiting 5 mins."
            time.sleep(5 * 60)


# Store tweets in a database
def store_tweets(cursor, db, collection_name):
    count = 0
    query_iterator = limit_cursor(cursor)
    for tweet in query_iterator:
        tweet_dict = tweet._json
        target_colection = db[collection_name]
        target_colection.insert_one(tweet_dict)
        count += 1
    return count


# Print out a little info about a list of tweets.  Used to confirm that the query worked.
def check_tweets(cursor):
    query_iterator = limit_cursor(cursor)
    for tweet in query_iterator:
        print "%s: %s" % (tweet.user.screen_name, tweet.created_at)


# Get the id of the first tweet in a database collection
def get_db_first(db, collection_name):
    if collection_name in db.collection_names():
        return db[collection_name].find().sort([("id", 1)]).limit(1).next()['id']
    else:
        return None


# Get the id of the last tweet in a database collection
def get_db_last(db, collection_name):
    if collection_name in db.collection_names():
        return db[collection_name].find().sort([("id", -1)]).limit(1).next()['id']
    else:
        return None
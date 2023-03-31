import pickle
import re

import pymysql
import tweepy
from flask import Flask, request, redirect, url_for, render_template, session
from nltk import WordNetLemmatizer

app = Flask(__name__)
app.secret_key = 'qwertyasdfg'
conn = pymysql.connect(host="localhost",
                       user="root",
                       password="Rv@091003",
                       database="login"
                       )

##Twitter App Config
consumer_key = 'REoUZtEfXYNWg0JvazLREN0SR'
consumer_secret = 'ul0ToBUYTsvhWqbbD0KuqZlGplCFZiPoGr81BVjelvQF93QjyL'
access_token = '956856733-gYTOyGLYaEmLkYEsBhbb2ibzlghfYxZDO6SjpA8l'
access_token_secret = '1uWquqIyWtS2JtpOvNgeVCRBjYVEj7bbLZH8wv8pxfB8V'
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    msg = ''
    print('test1')
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        print('Test2')
        username = request.form['username']
        password = request.form['password']
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM acc WHERE username=%s AND password=%s', (username, password,))
        account = cursor.fetchone()
        print(account)
        if account:
            session['loggedin'] = True
            session['id'] = account[1]
            session['username'] = account[1]
            msg = 'Logged in successfully !'
            return render_template('home.html', msg=msg)
        else:
            msg = 'Incorrect username / password !'
    return render_template('login.html', msg=msg)


@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


def preprocess(textdata):
    processedText = []

    wordLemm = WordNetLemmatizer()

    urlPattern = r"((http://)[^ ]*|(https://)[^ ]*|( www\.)[^ ]*)"
    userPattern = '@[^\s]+'
    alphaPattern = "[^a-zA-Z0-9]"
    sequencePattern = r"(.)\1\1+"
    seqReplacePattern = r"\1\1"
    emojis = {':)': 'smile', ':-)': 'smile', ';d': 'wink', ':-E': 'vampire', ':(': 'sad', ':-(': 'sad', ':-<': 'sad',
              ':P': 'raspberry', ':O': 'surprised', ':-@': 'shocked', ':@': 'shocked', ':-$': 'confused',
              ':\\': 'annoyed',
              ':#': 'mute', ':X': 'mute', ':^)': 'smile', ':-&': 'confused', '$_$': 'greedy', '@@': 'eyeroll',
              ':-!': 'confused', ':-D': 'smile', ':-0': 'yell', 'O.o': 'confused', '<(-_-)>': 'robot', 'd[-_-]b': 'dj',
              ":'-)": 'sadsmile', ';)': 'wink', ';-)': 'wink', 'O:-)': 'angel', 'O*-)': 'angel', '(:-D': 'gossip',
              '=^.^=': 'cat'}

    stopwordlist = ['a', 'about', 'above', 'after', 'again', 'ain', 'all', 'am', 'an', 'and', 'any', 'are', 'as', 'at',
                    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'by', 'can', 'd', 'did',
                    'do',
                    'does', 'doing', 'down', 'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have',
                    'having', 'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if', 'in',
                    'into', 'is', 'it', 'its', 'itself', 'just', 'll', 'm', 'ma', 'me', 'more', 'most', 'my', 'myself',
                    'now', 'o', 'of', 'on', 'once', 'only', 'or', 'other', 'our', 'ours', 'ourselves', 'out', 'own',
                    're',
                    's', 'same', 'she', "shes", 'should', "shouldve", 'so', 'some', 'such', 't', 'than', 'that',
                    "thatll",
                    'the', 'their', 'theirs', 'them', 'themselves', 'then', 'there', 'these', 'they', 'this', 'those',
                    'through', 'to', 'too', 'under', 'until', 'up', 've', 'very', 'was', 'we', 'were', 'what', 'when',
                    'where', 'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'won', 'y', 'you', "youd", "youll",
                    "youre", "youve", 'your', 'yours', 'yourself', 'yourselves']

    textdata = textdata.lower()
    textdata = re.sub(urlPattern, ' URL', textdata)
    for emoji in emojis.keys():
        textdata = textdata.replace(emoji, "EMOJI" + emojis[emoji])
    textdata = re.sub(userPattern, ' USER', textdata)
    textdata = re.sub(alphaPattern, " ", textdata)
    textdata = re.sub(sequencePattern, seqReplacePattern, textdata)

    tweetwords = ''
    for word in textdata.split():
        if word not in stopwordlist:
            if len(word) > 1:
                word = wordLemm.lemmatize(word)
                tweetwords += (word + ' ')

    processedText.append(tweetwords)

    return processedText


def load_models():
    file = open('vectoriser-ngram.pkl', 'rb')
    vectoriser = pickle.load(file)
    file.close()
    file = open('model.pkl', 'rb')
    LRmodel = pickle.load(file)
    file.close()

    return vectoriser, LRmodel


@app.route("/predict", methods=["GET", "POST"])
def predict():
    if request.method == "POST":
        tw_link = request.form['link']
        t_id = re.search("(?<=status\/).*", tw_link)
        if t_id:
            t_id = t_id.group(0)
            tweet_id = api.get_status(t_id).id
            tweet = api.get_status(tweet_id)
            tweet = tweet.text
        else:
            print("Bad Request - Client Side")

        vectoriser, LRmodel = load_models()
        textdata = vectoriser.transform(preprocess(tweet))
        sentiment = LRmodel.predict(textdata)
        sentiment = "Positive" if sentiment else "Negative"
    return render_template("home.html", sentiment=sentiment, tweet = tweet)


if __name__ == '__main__':
    app.run(debug=True)

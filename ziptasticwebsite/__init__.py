from flask import Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = "There's something around the corner"
import ziptasticwebsite.views

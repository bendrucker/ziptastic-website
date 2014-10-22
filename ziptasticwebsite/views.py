from ziptasticwebsite import app
from flask import render_template, request, flash, session, redirect, url_for
from forms import SignupForm, LoginForm
from redis import Redis
import hashlib, datetime


def generate_key(domain):
    salt = "There are better things around the corner..."
    key = hashlib.sha256()
    key.update(domain+salt)

    return key.hexdigest()


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()

    if request.method == 'POST':
        if form.validate() == False:
            return render_template('signup.html', form=form)
        else:
            redis_user = Redis(host='localhost', port=8322, db=1)

            # user_key = hashlib.sha256()
            # user_key.update(form.email.data + datetime.datetime.now().isoformat())
            user = {}
            user['email'] = form.email.data
            user['password'] = form.password.data # TODO: Dude raw passwords are bad.
            user['domain'] = form.domain.data

            redis_user.hmset('users:' + form.email.data, user)

            api_key = generate_key(form.domain.data)

            features = {}
            features['ziptastic_account'] = 'true'
            features['usage'] = 0
            redis_user.hmset('features:' + form.domain.data + ":" + api_key, features)


            return render_template('signup_complete.html')


    return render_template('signup.html', form=form)



@app.route('/dashboard', methods=['GET'])
def dashboard():
    user_email = session['user']['email']
    redis_user = Redis(host='localhost', port=8322, db=1)
    # features = redis_user.hgetall('features:' + hostname + ":" + api_key)
    user = redis_user.hgetall('users:' + user_email)

    return render_template('dashboard.html', welcome=user_email, user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate() == False:
            return render_template('login.html', form=form)
        else:
            redis_user = Redis(host='localhost', port=8322, db=1)
            user = redis_user.hgetall('users:' + form.email.data)
            print user

            # TODO: Hash before release!
            password = form.password.data

            if user is not None:
                if user['password'] == password:
                    session['user'] = user
                    print 'Redirecting to ' + url_for('dashboard')
                    return redirect(url_for('dashboard'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

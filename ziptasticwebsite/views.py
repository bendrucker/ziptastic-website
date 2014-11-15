from ziptasticwebsite import app
from flask import render_template, request, flash, session, redirect, url_for
from forms import SignupForm, LoginForm
from redis import Redis
import hashlib, datetime, json


def generate_key(domain):
    salt = "There are better things around the corner..."
    key = hashlib.sha256()
    key.update(domain+salt)

    return key.hexdigest()


def add_domain(user, domain, r):
    domains = r.hgetall('domains:' + user['email'] + ":*")
    print domains
    for check_domain in domains:
        print check_domain
        if check_domain.domain == domain:
            print "Domain already exists"
            return

    new_domain = {}
    new_domain['domain'] = domain

    r.hmset('domains:' + user['email'] + ':' + domain, new_domain)


    api_key = generate_key(domain)

    features = {}
    features['ziptastic'] = {}

    features['ziptastic']['service'] = "Ziptastic"
    features['ziptastic']['active'] = True
    features['ziptastic']['usage'] = 0
    features['ziptastic']['usage_limit'] = 2000

    # Example for another service.
    features['ziptastic']['service'] = "Connotation"
    features['connotation'] = {}
    features['connotation']['active'] = False

    r.hmset('features:' + domain + ":" + api_key, features)

    return True


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

            redis_user.hmset('users:' + form.email.data, user)

            # TODO: Add check to make sure it was successful.
            add_domain(user, form.domain.data, redis_user)

            return render_template('signup_complete.html', user=user)


    return render_template('signup.html', form=form)


@app.route('/dashboard', methods=['GET'])
def dashboard():
    user_email = session['user']['email']
    redis_user = Redis(host='localhost', port=8322, db=1)

    user = redis_user.hgetall('users:' + user_email)
    domain_keys = redis_user.keys('domains:' + user_email + ':*')
    domains = []

    for domain_key in domain_keys:
        domain = redis_user.hgetall(domain_key)
        features_keys = redis_user.keys('features:' + domain.get('domain') + '*')
        features = redis_user.hgetall(features_keys[0])
        domain['features'] = {}

        for feature_key, feature_data in features.iteritems():
            # print feature_key
            feature_data = eval(feature_data)
            domain['features'][feature_key] = feature_data

        print domain
        domains.append(domain)

    return render_template('dashboard.html',
                            welcome=user_email,
                            user=user,
                            domains=domains
                            )


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

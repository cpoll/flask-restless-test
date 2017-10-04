from flask import render_template, request, redirect
from flask_security import Security, logout_user, login_required
from flask_security.utils import encrypt_password, verify_password
from flask_restless import APIManager
from flask_jwt import JWT, jwt_required, current_identity

from database import db
from application import app
from models import User, SomeStuff, user_datastore
from admin import init_admin

# Setup Flask-Security  =======================================================
security = Security(app, user_datastore)

# Views  ======================================================================
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/mypage')
@login_required
def mypage():
    return render_template('mypage.html')


@app.route('/logout')
def log_out():
    logout_user()
    return redirect(request.args.get('next') or '/')


# JWT Token authentication  ===================================================
def authenticate(username, password):
    print(username, password)
    user = user_datastore.find_user(email=username)
    if user and username == user.email and verify_password(password, user.password):
        return user
    return None


def load_user(payload):
    print(payload)
    user = user_datastore.find_user(id=payload['identity'])
    return user


jwt = JWT(app, authenticate, load_user)

# Flask-Restless API  =========================================================
@jwt_required()
def auth_func(**kw):
    pass

def dumb_prefunc(**kw):
    print("dumb prefunc keywords:", kw)
    print("prefunc identity: ", current_identity)

def dumb_postfunc(**kw):
    print("dumb postfunc keywords:", kw)
    print("postfunc identity: ", current_identity)

pp=[dumb_prefunc, auth_func, dumb_postfunc]

apimanager = APIManager(app, flask_sqlalchemy_db=db)
apimanager.create_api(
    SomeStuff,
    methods=['GET', 'POST', 'DELETE', 'PUT'],
    url_prefix='/api/v1',
    collection_name='free_stuff',
    include_columns=['id', 'data1', 'data2', 'user_id'])
apimanager.create_api(
    SomeStuff,
    methods=['GET', 'POST', 'DELETE', 'PUT'],
    url_prefix='/api/v1',
    preprocessors=dict(GET_SINGLE=pp, GET_MANY=pp, POST=pp),
    collection_name='protected_stuff',
    include_columns=['id', 'data1', 'data2', 'user_id'])


# Setup Admin  ================================================================
init_admin()


# Bootstrap  ==================================================================
def create_test_models():
    user_datastore.create_user(email='test', password=encrypt_password('test'))
    user_datastore.create_user(email='test2', password=encrypt_password('test2'))
    stuff = SomeStuff(data1=2, data2='toto', user_id=1)
    db.session.add(stuff)
    stuff = SomeStuff(data1=5, data2='titi', user_id=1)
    db.session.add(stuff)
    db.session.commit()


@app.before_first_request
def bootstrap_app():
    if not app.config['TESTING']:
        if db.session.query(User).count() == 0:
            create_test_models()


# Start server  ===============================================================
if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run()

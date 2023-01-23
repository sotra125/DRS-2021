import pickle

import jsonpickle
from flask import request, session

from engine.config import CURRENCY_NAMES
from engine.application_data import app, db
from engine.utility import get_crypto_prices, hash_text, deactivate_currency, activate_currency
from engine.models.user import User
from engine.models.account import Account
from engine.models.transaction import Transaction


# <editor-fold desc="Home Routes">

@app.route('/')
def home():
    db.create_all()

    # fetch account data
    account: Account = Account()
    if 'user' in request.form:
        account = Account.query.filter_by(user_id=request.form['user']).first()

    # fetch crypto prices data
    crypto_prices = get_crypto_prices()

    return app.response_class(response=pickle.dumps({
        'account': jsonpickle.encode(account),
        'crypto_prices': crypto_prices
    }),
        status=200,
        mimetype='application/json')


# </editor-fold>


# <editor-fold desc="User Routes">


@app.route('/user/register', methods=['POST'])
def register():
    try:
        form_data = request.form
        user: User = User()

        # create user with inputted data
        user.email = form_data['email']
        user.password = hash_text(form_data['password'])
        user.user_id = hash_text(form_data['email'])
        user.name = form_data['name']
        user.last_name = form_data['last_name']
        user.address = form_data['address']
        user.city = form_data['city']
        user.country = form_data['country']
        user.phone_number = form_data['phone_number']
        user.is_verified = False

        if isinstance(User.query.filter_by(email=user.email).first(), User):
            return app.response_class(response=pickle.dumps({
                'message': 'An account with that email already exists!'
            }),
                status=400,
                mimetype='application/json')

        account: Account = Account()
        account.user_id = user.user_id

        # add user to db
        db.session.add(user)
        db.session.add(account)
        db.session.commit()

        return app.response_class(response=pickle.dumps({}),
                                  status=200,
                                  mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


@app.route('/user/login', methods=['POST'])
def login():
    try:
        form_data = request.form
        email, password = form_data['email'], form_data['password']

        user = User.query.filter_by(email=email).first()
        if not isinstance(user, User):
            return app.response_class(response=pickle.dumps({
                'message': 'An account with that email does not exist!'
            }),
                status=400,
                mimetype='application/json')
        if user.password != hash_text(password):
            return app.response_class(response=pickle.dumps({
                'message': 'Wrong password!'
            }),
                status=400,
                mimetype='application/json')

        session['user'] = user.user_id
        session['is_verified'] = 'True' if user.is_verified else 'False'
        return app.response_class(response=pickle.dumps({
            'user': user.user_id,
            'is_verified': 'True' if user.is_verified else 'False'
        }),
            status=200,
            mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


@app.route('/user/verify-account', methods=['POST'])
def verify_account():
    form_data = request.form
    if '4242424242424242' != f'{form_data["number_1"]}{form_data["number_2"]}{form_data["number_3"]}{form_data["number_4"]}' or \
            'Name' != form_data['name'] or \
            '02/23' != f'{form_data["expiration_date_month"]}/{form_data["expiration_date_year"]}' or \
            '123' != form_data['security_code']:
        return app.response_class(response=pickle.dumps({
            'message': 'Entered credit card is invalid!'
        }),
            status=400,
            mimetype='application/json')

    try:
        user = User.query.filter_by(user_id=request.form['user']).first()
        user.is_verified = True
        db.session.commit()

        return app.response_class(response=pickle.dumps({}),
                                  status=200,
                                  mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


@app.route('/user/get')
def get_user():
    try:
        user = User.query.filter_by(user_id=request.form['user']).first()
        return app.response_class(response=pickle.dumps({
            'user': jsonpickle.encode(user)
        }),
            status=200,
            mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


@app.route('/user/update_profile', methods=['GET', 'POST'])
def update_profile():
    form_data = request.form

    user = User.query.filter_by(user_id=form_data['user']).first()
    user.name = form_data['name']
    user.last_name = form_data['last_name']
    user.address = form_data['address']
    user.city = form_data['city']
    user.country = form_data['country']
    user.phone_number = form_data['phone_number']

    try:
        db.session.commit()
        return app.response_class(response=pickle.dumps({}),
                                  status=200,
                                  mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


@app.route('/user/account')
def get_account():
    try:
        account = Account.query.filter_by(user_id=request.form['user']).first()
        return app.response_class(response=pickle.dumps({
            'account': jsonpickle.encode(account)
        }),
            status=200,
            mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


@app.route('/user/update_currencies', methods=['GET', 'POST'])
def update_currencies():
    try:
        form_data = request.form
        account = Account.query.filter_by(user_id=form_data['user']).first()

        for currency in CURRENCY_NAMES:
            if currency not in form_data:
                successful = deactivate_currency(account, currency)
                if not successful:
                    raise Exception(f'Failed to deactivate {currency}!')
            else:
                activate_currency(account, currency)

        db.session.commit()
        return app.response_class(response=pickle.dumps({}),
                                  status=200,
                                  mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


# </editor-fold>


# <editor-fold desc="Funds Routes">


@app.route('/funds/deposit', methods=['GET', 'POST'])
def deposit():
    try:
        # extract data from form
        form_data = request.form
        amount = round(float(form_data['amount']), 2)

        if amount <= 0:
            return app.response_class(response=pickle.dumps({
                'message': 'Invalid value entered!'
            }),
                status=400,
                mimetype='application/json')

        # add amount to account
        account = Account.query.filter_by(user_id=form_data['user']).first()
        account.usd_balance += amount

        db.session.commit()
        return app.response_class(response=pickle.dumps({}),
                                  status=200,
                                  mimetype='application/json')
    except:  # NOQA
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while processing your request!'
        }),
            status=400,
            mimetype='application/json')


# </editor-fold>


if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)

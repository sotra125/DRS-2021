import pickle
from _operator import attrgetter
from datetime import datetime

import jsonpickle
from flask import request, session
from sqlalchemy import or_

from engine.config import CURRENCY_NAMES, ACCOUNT_BALANCE_TO_CURRENCY_NAMES_MAP
from engine.application_data import app, db
from engine.utility import get_crypto_prices, hash_text, deactivate_currency, activate_currency, convert, \
    get_hashed_transaction_id
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


@app.route('/funds/transfer', methods=['GET', 'POST'])
def transfer():
    try:
        # extract data from form
        form_data = request.form
        from_currency = form_data['from_currency']
        to_currency = form_data['to_currency']
        amount = round(float(form_data['amount']), 7)

        if amount <= 0:
            return app.response_class(response=pickle.dumps({
                'message': 'Enter a valid amount!'
            }),
                status=400,
                mimetype='application/json')

        if from_currency == to_currency:
            return app.response_class(response=pickle.dumps({
                'message': "Can't transfer into same currency!"
            }),
                status=400,
                mimetype='application/json')

        # check if user has sufficient funds in that currency to transfer
        account = Account.query.filter_by(user_id=form_data['user']).first()
        if account.__getattribute__(from_currency) < amount:
            return app.response_class(response=pickle.dumps({
                'message': 'Insufficient funds!'
            }),
                status=400,
                mimetype='application/json')

        # equalize funds
        to_currency_amount = convert(from_currency, to_currency, amount)
        account.__setattr__(from_currency, account.__getattribute__(from_currency) - amount)
        account.__setattr__(to_currency, account.__getattribute__(to_currency) + to_currency_amount)

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


@app.route('/funds/send', methods=['GET', 'POST'])
def send():
    try:
        # extract data from form
        form_data = request.form
        receiver_email = form_data['receiver']
        currency = form_data['currency']
        amount = round(float(form_data['amount']), 7)
        sender_account = Account.query.filter_by(user_id=form_data['user']).first()

        if amount <= 0:
            return app.response_class(response=pickle.dumps({
                'message': 'Enter a valid amount!'
            }),
                status=400,
                mimetype='application/json')

        receiver_user = User.query.filter_by(email=receiver_email).first()
        if not isinstance(receiver_user, User):
            return app.response_class(response=pickle.dumps({
                'message': "User doesn't exist!"
            }),
                status=400,
                mimetype='application/json')

        if receiver_user.user_id == form_data['user']:
            return app.response_class(response=pickle.dumps({
                'message': "Can't send funds to self!"
            }),
                status=400,
                mimetype='application/json')
        receiver_account = Account.query.filter_by(user_id=receiver_user.user_id).first()

        # check if user has sufficient funds in that currency to send
        if sender_account.__getattribute__(currency) < amount:
            return app.response_class(response=pickle.dumps({
                'message': 'Insufficient funds!'
            }),
                status=400,
                mimetype='application/json')

        if currency != 'usd_balance' and not receiver_account.__getattribute__(f'{currency[:3]}_enabled'):
            return app.response_class(response=pickle.dumps({
                'message': "Recipient doesn't have that currency active!"
            }),
                status=400,
                mimetype='application/json')

        # equalize funds
        sender_account.__setattr__(currency, sender_account.__getattribute__(currency) - amount)
        receiver_account.__setattr__(currency, receiver_account.__getattribute__(currency) + amount)

        # add transaction into db
        sender_user = User.query.filter_by(user_id=form_data['user']).first()
        transaction = Transaction()  # NOQA 3104
        transaction.id = get_hashed_transaction_id(sender_user.email, receiver_user.email, amount=amount)
        transaction.sender = sender_user.email
        transaction.currency = ACCOUNT_BALANCE_TO_CURRENCY_NAMES_MAP[currency]
        transaction.receiver = receiver_user.email
        transaction.amount = amount
        transaction.date = datetime.now()
        transaction.state = 'Processing'
        db.session.add(transaction)

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


# <editor-fold desc="Transaction Routes">


@app.route('/transaction/all')
def get_all_transactions():
    transactions = get_transactions(request.form['user'])
    encoded_transactions = []
    for transaction in transactions:
        encoded_transactions.append(jsonpickle.encode(transaction))

    return app.response_class(response=pickle.dumps(encoded_transactions),
                              status=200,
                              mimetype='application/json')


@app.route('/transaction/history')
def transactions_history():
    # fetch transaction data
    transactions = get_transactions(request.form['user'])
    if transactions is None:
        return app.response_class(response=pickle.dumps({
            'message': 'An error occurred while fetching data!'
        }),
            status=400,
            mimetype='application/json')

    # sort fetched data
    sort_transactions(transactions, request.form['sort'], request.form['order'])

    # filter fetched data
    filtered_transactions = filter_transactions(transactions, request.form['search'])
    if filtered_transactions is not None:
        transactions = filtered_transactions.copy()

    encoded_transactions = []
    for transaction in transactions:
        encoded_transactions.append(jsonpickle.encode(transaction))

    return app.response_class(response=pickle.dumps(encoded_transactions),
                              status=200,
                              mimetype='application/json')


def get_transactions(user_id):
    """
    Fetches transactions from db.
    :return: List of transactions or None in case of exception
    """
    try:

        user = User.query.filter_by(user_id=user_id).first()

        return Transaction.query.filter(or_(
            Transaction.sender.like(user.email),
            Transaction.receiver.like(user.email)
        )).all()
    except:  # NOQA
        return None


def sort_transactions(transactions: list, sort: str, order: str) -> None:
    """
    Sorts transactions according to the sort category and order.
    :param transactions: List of transactions to sort
    :param sort: Sorting category
    :param order: Sorting order
    :return: None
    """
    try:
        if sort != 'default':
            transactions.sort(key=attrgetter(sort), reverse=order == 'true')
        else:
            transactions.sort(key=attrgetter('date'), reverse=order == 'true')
    except:  # NOQA
        pass


def filter_transactions(transactions: list, search: str):
    """
    Filters transactions according to the search term if anything was searched.
    :param transactions: List of transactions to sort
    :param search: Search term enter with form
    :return: Returns filtered list of transactions or None if an exception was raised during filtering.
    """
    try:
        if search != 'default' and search != '':
            return list(filter(
                lambda transaction: transaction.sender.find(search) != -1 or transaction.receiver.find(
                    search) != -1, transactions)).copy()
    except:  # NOQA
        return False


# </editor-fold>


if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)

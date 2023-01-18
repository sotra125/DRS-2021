import pickle

import jsonpickle
from flask import request

from utility import *
from application_data import app, db
from models.user import User
from models.account import Account
from models.transaction import Transaction


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


if __name__ == '__main__':
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=True)

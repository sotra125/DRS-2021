import json
import pickle
from types import SimpleNamespace

from flask_toastr import Toastr

from flask import Flask, render_template, session
import requests

app = Flask(__name__)
app.secret_key = 'hs47@53Le14LI$Vg'
toastr = Toastr()
toastr.init_app(app)  # initialize toastr on the app


# <editor-fold desc="Home Routes">


@app.route('/')
def home():
    if 'user' not in session:
        session['user'] = None
    if 'is_verified' not in session:
        session['is_verified'] = None
    response = requests.get('http://127.0.0.1:5001', data={'user': session['user']})
    response_data = pickle.loads(response.content)
    return render_template('index.html', account=json.loads(response_data['account'],
                                                            object_hook=lambda x: SimpleNamespace(**x)),
                           crypto_prices=response_data['crypto_prices'])


# </editor-fold>


if __name__ == '__main__':
    app.run(debug=True)

import json
import pickle
from types import SimpleNamespace

from flask_toastr import Toastr

from flask import Flask, render_template, session, request, flash, url_for, redirect
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


# <editor-fold desc="User Routes">


@app.route('/user/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    response = requests.post('http://127.0.0.1:5001/user/register', data=request.form)

    # OK
    if response.status_code == 200:
        flash('Successfully registered', 'message')
        return render_template('login.html')

    # BAD REQUEST
    flash(pickle.loads(response.content)['message'], 'error')
    return render_template('register.html')


@app.route('/user/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    response = requests.post('http://127.0.0.1:5001/user/login', data=request.form)

    # OK
    if response.status_code == 200:
        response_data = pickle.loads(response.content)
        session['user'] = response_data['user']
        session['is_verified'] = response_data['is_verified']
        return redirect(url_for('home'))

    # BAD REQUEST
    flash(pickle.loads(response.content)['message'], 'error')
    return render_template('login.html')


@app.route('/user/sign-out')
def sign_out():
    if 'user' in session:
        session['user'] = None
    if 'is_verified' in session:
        session['is_verified'] = None
    return redirect(url_for('home'))


@app.route('/user/verify-account', methods=['GET', 'POST'])
def verify_account():
    if request.method == 'GET':
        # check session for logged-in user
        if 'user' not in session:
            return render_template('login.html')

        return render_template('verify-account.html')

    # check session for logged-in user
    if 'user' not in session:
        return render_template('login.html')

    data = request.form.copy().to_dict(flat=False)
    data['user'] = session['user']

    response = requests.post('http://127.0.0.1:5001/user/verify-account', data=data)

    # OK
    if response.status_code == 200:
        session['is_verified'] = 'True'
        flash('Account Verified!', 'message')
        return redirect(url_for('home'))

    # BAD REQUEST
    flash(pickle.loads(response.content)['message'], 'error')
    return render_template('verify-account.html')


@app.route('/user/update_profile', methods=['GET', 'POST'])
def update_profile():
    if request.method == 'GET':
        # check session for logged-in user
        if 'user' not in session:
            return render_template('login.html')

        user = get_user()
        return render_template('edit-profile.html', user=user)

    # check session for logged-in user
    if 'user' not in session:
        return render_template('login.html')

    data = request.form.copy().to_dict(flat=False)
    data['user'] = session['user']

    response = requests.post('http://127.0.0.1:5001/user/update_profile', data=data)

    # OK
    if response.status_code == 200:
        flash('Account information updated', 'message')
        return redirect(url_for('home'))

    # BAD REQUEST
    flash(pickle.loads(response.content)['message'], 'error')
    user = get_user()
    return render_template('edit-profile.html', user=user)


@app.route('/user/update_currencies', methods=['GET', 'POST'])
def update_currencies():
    if request.method == 'GET':
        # check session for logged-in user
        if 'user' not in session:
            return render_template('login.html')

        account = get_account()
        return render_template('select-currencies.html', account=account)

    # check session for logged-in user
    if 'user' not in session:
        return render_template('login.html')

    data = request.form.copy().to_dict(flat=False)
    data['user'] = session['user']

    response = requests.post('http://127.0.0.1:5001/user/update_currencies', data=data)

    # OK
    if response.status_code == 200:
        flash('Account information updated', 'message')
        return redirect(url_for('home'))

    # BAD REQUEST
    flash(pickle.loads(response.content)['message'], 'error')
    account = get_account()
    return render_template('select-currencies.html', account=account)


# </editor-fold>


# <editor-fold desc="Other">


def get_user():
    response = requests.get('http://127.0.0.1:5001/user/get', data={'user': session['user']})
    if response.status_code == 200:
        response_data = pickle.loads(response.content)
        user = json.loads(response_data['user'], object_hook=lambda x: SimpleNamespace(**x))
        return user

    return None


def get_account():
    response = requests.get('http://127.0.0.1:5001/user/account', data={'user': session['user']})
    if response.status_code == 200:
        response_data = pickle.loads(response.content)
        account = json.loads(response_data['account'], object_hook=lambda x: SimpleNamespace(**x))
        return account

    return None


# </editor-fold>

if __name__ == '__main__':
    app.run(debug=True)

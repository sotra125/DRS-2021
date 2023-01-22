from engine.application_data import db


class Account(db.Model):
    user_id = db.Column(db.String, primary_key=True)
    usd_balance = db.Column(db.Float, default=0)

    btc_balance = db.Column(db.Float, default=0)  # Bitcoin
    btc_enabled = db.Column(db.Boolean, default=True)

    eth_balance = db.Column(db.Float, default=0)  # Ethereum
    eth_enabled = db.Column(db.Boolean, default=True)

    bnb_balance = db.Column(db.Float, default=0)  # BNB
    bnb_enabled = db.Column(db.Boolean, default=True)

    pol_balance = db.Column(db.Float, default=0)  # Polygon
    pol_enabled = db.Column(db.Boolean, default=True)

    dog_balance = db.Column(db.Float, default=0)  # Dogecoin
    dog_enabled = db.Column(db.Boolean, default=True)

    ada_balance = db.Column(db.Float, default=0)  # Cardano
    ada_enabled = db.Column(db.Boolean, default=False)

    dot_balance = db.Column(db.Float, default=0)  # Polkadot
    dot_enabled = db.Column(db.Boolean, default=False)

from application_data import db


class Transaction(db.Model):
    __tablename__ = 'transactions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.String, primary_key=True)
    sender = db.Column(db.String, nullable=False)
    receiver = db.Column(db.String, nullable=False)
    currency = db.Column(db.String, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    state = db.Column(db.String, nullable=False)
    date = db.Column(db.String, nullable=False)

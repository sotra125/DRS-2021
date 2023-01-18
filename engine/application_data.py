from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_toastr import Toastr

app = Flask(__name__)
app.secret_key = 'hW47@55Le12LI$Vg'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db: SQLAlchemy = SQLAlchemy(app)
toastr = Toastr()
toastr.init_app(app)  # initialize toastr on the app

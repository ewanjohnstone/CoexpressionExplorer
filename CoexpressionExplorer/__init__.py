import os
from flask import Flask
import click


from CoexpressionExplorer.models import db, Dataset, DatasetMeta


# create and configure the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///CoExDB.db" 

db.init_app(app)
with app.app_context():
    db.create_all()


import CoexpressionExplorer.views
import CoexpressionExplorer.setup_db






        
        





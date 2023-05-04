import os
from flask import Flask


def create_app():
    # create and configure the app
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///CoExDB.db"
    #from . import database
    #import CoexpressionExplorer.models
    from CoexpressionExplorer.models import db
    db.init_app(app)

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'
    



    with app.app_context():
        db.create_all()

    return app






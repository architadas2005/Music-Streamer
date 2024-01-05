from flask import Flask, render_template, redirect, url_for, request
from app.database import db

app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///database.sqlite3"
app.config["UPLOAD_FOLDER"]='Uploads'
app.config['STATIC_FOLDER'] = 'Static'

db.init_app(app) 
app.app_context().push()

from app.controllers import *
#if __name__ == "__main__":
app.run(debug=True)
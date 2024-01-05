from flask_sqlalchemy import SQLAlchemy
db=SQLAlchemy()
class Admin(db.Model):
    id=db.Column(db.String, primary_key=True)
    password=db.Column(db.String)
class Users(db.Model):
    s_no=db.Column(db.Integer, autoincrement=True, primary_key=True)
    id=db.Column(db.String, nullable=False, unique=True)
    name=db.Column(db.String, nullable=False)
    password=db.Column(db.String, nullable=False)
class Creator(db.Model):
    c_id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    id=db.Column(db.String, unique=True)
    name=db.Column(db.String, nullable=False)
    password=db.Column(db.String, nullable=False)
    blacklist=db.Column(db.Integer,nullable=False)
    flaged=db.Column(db.Integer)
class Songs(db.Model):
    song_id=db.Column(db.Integer,primary_key=True, autoincrement=True)
    song_name=db.Column(db.String, nullable=False, unique=True)
    lyrics=db.Column(db.String, nullable=True)
    flag=db.Column(db.Integer, nullable=True)
    rating=db.Column(db.Integer, nullable=True)
    c_id=db.Column(db.Integer, db.ForeignKey("creator.c_id"))
class Album(db.Model):
    c_no=db.Column(db.Integer, db.ForeignKey("creator.c_id"))
    album_id=db.Column(db.Integer, primary_key=True, autoincrement=True)
    album_name=db.Column(db.String, unique=True, nullable=False)
    song=db.relationship("Songs", backref="myalbum", secondary="als")
class Playlist(db.Model):
    s_no=db.Column(db.Integer, db.ForeignKey("users.s_no"), nullable=False)
    playlist_id=db.Column(db.Integer,primary_key=True,nullable=False,autoincrement=True)
    playlist_name=db.Column(db.String, nullable=False)
    song=db.relationship("Songs", backref="play_list", secondary="pls")
class Pls(db.Model):
    i=db.Column(db.Integer, primary_key=True)
    playlist_id=db.Column(db.Integer, db.ForeignKey("playlist.playlist_id"))
    song_id=db.Column(db.Integer, db.ForeignKey("songs.song_id"))
class Als(db.Model):
    i=db.Column(db.Integer, primary_key=True)
    album_id=db.Column(db.Integer, db.ForeignKey("album.album_id"))
    song_id=db.Column(db.Integer, db.ForeignKey("songs.song_id"))
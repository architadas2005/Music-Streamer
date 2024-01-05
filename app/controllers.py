from flask import request, render_template, redirect, url_for, send_from_directory
from flask import current_app as app
from .database import *
from os.path import join,exists
from os import remove
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

@app.route('/', methods=["GET","POST"])
def home():
    if request.method=="GET":
        return render_template('index.html')
    user=request.form["button"]
    if user =="Admin":
        return render_template("admin.html",user="admin")
    elif user =="User":
        return render_template("user.html", user="user")
    else:
        return render_template("creator.html", user="creator")

@app.route("/login/<viewer>", methods=["POST"])
def login(viewer):
    user_id = request.form["id"]
    password = request.form["pass"]

    if viewer == "admin":
        # Check if the user is an admin
        ans = Admin.query.filter_by(id=user_id).first()
        if ans and password == ans.password:
            return redirect(url_for("admin"))
        return render_template("admin.html", user="admin", msg="User ID or password is incorrect")

    elif viewer == "creator":
        # Check if the user is a registered user first
        user_exists = Users.query.filter_by(id=user_id).first()
        if not user_exists:
            return render_template("creator.html", user="creator", msg="Please register as a user first.")

        # Check if the user is also a creator
        ans = Creator.query.filter_by(id=user_id).first()
        if ans and password == ans.password:
            c = Creator.query.filter_by(id=user_id).first()
            if c.blacklist == 1:
                return render_template("creator.html", user="creator", msg="Your ID has been blocked because of excessive flagged content")
            n = c.name
            myalbm = Album.query.filter_by(c_no=c.c_id).all()
            s = Songs.query.filter_by(c_id=c.c_id).all()
            return render_template('c_dash.html', myalbm=myalbm, mysongs=s, c=c.c_id, name=n)

        return render_template("creator.html", user="creator", msg="User ID or Password is incorrect")

    elif viewer == "user":
        ans = Users.query.filter_by(id=user_id).first()
        if ans and password == ans.password:
            u = Users.query.filter_by(id=user_id).first()
            play_list = Playlist.query.filter_by(s_no=u.s_no).all()
            song = Songs.query.order_by(Songs.rating.desc()).limit(10).all()
            albums = Album.query.limit(10).all()
            return render_template('u_dash.html', name=u.name, u=u.s_no, pls=play_list, songs=song, albums=albums)

        return render_template("user.html", user="user", msg="User ID or Password is incorrect")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        user_type = request.form.get('type')
        name = request.form['name']
        uid = request.form['id']
        pswd = request.form['pass']

        if user_type == 'creator':
            # Check if the user already exists
            if not Users.query.filter_by(id=uid).first():
                return render_template("signup.html", msg="Please register as a user first.")
            # Check if the creator with the same ID already exists
            if Creator.query.filter_by(id=uid).first():
                return render_template("signup.html", msg="Creator with this ID already exists.")

            # Register as a creator
            new_creator = Creator(id=uid, password=pswd, name=name, blacklist=0, flaged=0)
            db.session.add(new_creator)
            db.session.commit()
            return render_template("creator.html", user="creator")

        elif user_type == 'user':
            # Check if the user with the same ID already exists
            if Users.query.filter_by(id=uid).first():
                return render_template("signup.html", msg="User with this ID already exists.")

            # Register as a user
            new_user = Users(id=uid, password=pswd, name=name)
            db.session.add(new_user)
            db.session.commit()
            return render_template("user.html", user="user")

    return render_template("signup.html")

@app.route("/redirect/<types>/<int:id>")
def redi(types,id):
    if types=="creator":
        myalbm=Album.query.filter_by(c_no=id).all()
        s=Songs.query.filter_by(c_id=id).all()
        return render_template("c_dash.html", myalbm=myalbm, mysongs=s, c=id)
    if types=="user":
        play_list=Playlist.query.filter_by(s_no=id).all()
        song=Songs.query.order_by(Songs.rating.desc()).limit(10).all()
        albums=Album.query.limit(10).all()
        return render_template('u_dash.html',u=id,pls=play_list,songs=song,albums=albums)

@app.route('/<tpes>/album/<album_id>', methods=["GET","POST"])
def album(tpes, album_id):
    name=Album.query.filter_by(album_id=album_id).first()
    s=name.song
    v="hidden" if tpes=="user" else ""
    if request.method=="GET":
        return render_template('album.html', asongs=s, name=name, t=tpes, vis=v)
    else:
        search=request.form["search"]
        if search != None:
            try:    
                s=Songs.query.filter(Songs.song_name.ilike(f'%{search}%')).first()
                s_n=s if Als.query.filter_by(album_id=album_id,song_id=s.song_id).first() else False    
            except:
                s_n=False
            try:    
                s=Songs.query.filter_by(rating=search).all()
                s_r=list(filter(lambda x:Als.query.filter_by(album_id=album_id,song_id=x.song_id).first(),s))
            except:
                s_r=False
            return render_template('album.html',t=tpes, search=search, sn=s_n,sr=s_r, name=name, vis=v)
        else:
            return render_template('album.html', asongs=s, name=name, t=tpes, vis=v)

@app.route('/del/<tpes>/<int:id>')
def delete(tpes, id):
    if tpes=="album":
        a=Album.query.filter_by(album_id=id).first()
        c=a.c_no
        for rel in Als.query.filter_by(album_id=id).all():
            db.session.delete(rel)
        db.session.delete(a)
        db.session.commit()
        return redirect(f"/redirect/creator/{c}")
    if tpes=="song":
        d=Songs.query.filter_by(song_id=id).first()
        c=d.c_id
        file=join(app.config["UPLOAD_FOLDER"],(d.song_name + ".mp3"))
        if exists(file):
            remove(file)
        db.session.delete(d)
        for s in Als.query.filter_by(song_id=id).all():
            db.session.delete(s)
        for s in Pls.query.filter_by(song_id=id).all():
            db.session.delete(s)
        db.session.commit()
        return redirect(f"/redirect/creator/{c}")
    if tpes=="playlist":
        p=Playlist.query.filter_by(playlist_id=id).first()
        u=p.s_no
        for rel in Pls.query.filter_by(playlist_id=id).all():
            db.session.delete(rel)
        db.session.delete(p)
        db.session.commit()
        return redirect(f"/redirect/user/{u}")

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/add_song/<int:id>", methods=["POST"])
def upload(id):
    song_name=request.form["song_name"]
    lyrics=request.form["lyrics"]
    file=request.files["audio"]
    ns=Songs(song_name=song_name, lyrics=lyrics,rating=0, c_id=id)
    db.session.add(ns)
    try:
        db.session.commit()
    except:
        m="Sorry! Song with the given name already exists.\nPlease try a different name."
        return render_template("add_song.html",c_id=id,msg=m)
    file.save(join(app.config["UPLOAD_FOLDER"],(song_name + ".mp3")))
    return redirect(f'/redirect/creator/{id}')

@app.route('/c_handle/<int:id>', methods=["POST"])
def c_handle(id):
    return render_template("add_song.html", c_id=id)

@app.route('/song/<int:sid>/<tpes>/<int:id>')
def sing(sid,tpes,id):
    s=Songs.query.filter_by(song_id=sid).first()
    return render_template("song.html", song=s, tpes=tpes,id=id)

@app.route("/song/mod/<int:song_id>", methods=["POST"])
def msong(song_id):
    l=request.form["lyrics"]
    s=Songs.query.filter_by(song_id=song_id).first()
    s.lyrics=l
    db.session.commit()
    return redirect(f"/song/{song_id}/creator/{s.c_id}")

@app.route("/song/er/<int:song_id>/<id>", methods=["POST"])
def esong(song_id,id):
    s=Songs.query.filter_by(song_id=song_id).first()
    try:
        is_flag=request.form["flag"]
        s.flag=1
    except:
        s.flag=0
    rate=request.form["rating"]
    if rate:
        s.rating=rate
    db.session.commit()
    return redirect(f"/song/{song_id}/user/{id}")

@app.route('/song/<tpes>/<int:id>', methods=["GET","POST"])
def view_song(tpes,id):
    if tpes=='creator':
        s=Songs.query.filter_by(c_id=id).all()
        if request.method=="GET":
            return render_template('view_songs.html', t=tpes, id=id, songs=s)
        srch=request.form["search"]
        ss=Songs.query.filter(Songs.song_name.ilike(f'%{srch}%')).all()
        r=Songs.query.filter_by(rating=srch).all()
        return render_template('view_songs.html',n=ss,r=r, t=tpes, search=srch, id=id, songs=s)
    elif tpes=='user':
            s=Songs.query.all() 
            if request.method=="GET":
                return render_template('view_songs.html',t=tpes,id=id,songs=s)
            srch=request.form["search"]
            ss=Songs.query.filter(Songs.song_name.ilike(f'%{srch}%')).all()
            r=Songs.query.filter_by(rating=srch).all()
            return render_template('view_songs.html',n=ss,r=r, t=tpes, search=srch, id=id,songs=s)
    elif tpes=='admin':
        s=Songs.query.filter_by(song_id=id).first()
        return render_template('song_check.html',song=s)

@app.route('/album/<tpes>/<int:id>', methods=["GET","POST"])
def view_album(tpes,id):
    if tpes=='creator':
        albums=Album.query.filter_by(c_no=id).all()
        if request.method=="GET":
            return render_template('view_album.html', t=tpes, id=id, albms=albums)
        srch=request.form["search"]
        sa=Album.query.filter(Album.album_name.ilike(f'%{srch}%')).all()
        return render_template('view_album.html',n=sa, t=tpes, search=srch, id=id, albms=albums)
    elif tpes=='user':
        albums=Album.query.all() 
        if request.method=="GET":
            return render_template('view_album.html',t=tpes,id=id,albms=albums)
        srch=request.form["search"]
        ss=Album.query.filter(Album.album_name.ilike(f'%{srch}%')).all()
        return render_template('view_album.html',n=ss, t=tpes, search=srch, id=id,albms=albums)

@app.route('/create_playlist/<int:id>', methods=["GET","POST"])
def c_playlist(id):
    if request.method=="GET":
        s=Songs.query.all()
        return render_template('create_playlist.html', songs=s, u_id=id)
    p_name=request.form["p_name"]
    psongs=request.form.getlist("song")
    p=Playlist(s_no=id, playlist_name=p_name)
    db.session.add(p)
    db.session.commit()
    for song in psongs:
        psong=Pls(playlist_id=p.playlist_id, song_id=song)
        db.session.add(psong)
    db.session.commit()
    return redirect(f"/redirect/user/{id}")

@app.route('/user/playlist/<int:id>')
def play_list(id):
    p=Playlist.query.filter_by(playlist_id=id).first()
    s=p.song
    return render_template('playlist.html',psongs=s,p=p)

@app.route('/modify_playlist/<int:id>', methods=["GET", "POST"])
def modify_playlist(id):
    if request.method == "GET":
        p = Playlist.query.filter_by(playlist_id=id).first()
        s = Songs.query.all()
        return render_template('modify_playlist.html', playlist=p, songs=s)

    if request.method == "POST":
        p_name = request.form["p_name"]
        psongs = request.form.getlist("song")

        # Update playlist details
        playlist = Playlist.query.filter_by(playlist_id=id).first()
        playlist.playlist_name = p_name

        # Clear existing songs in the playlist
        Pls.query.filter_by(playlist_id=id).delete()

        # Add selected songs to the playlist
        for song in psongs:
            psong = Pls(playlist_id=id, song_id=song)
            db.session.add(psong)

        db.session.commit()

        return redirect(f"/redirect/user/{playlist.s_no}")

@app.route('/create_album/<int:id>', methods=["GET","POST"])
def c_album(id):
    if request.method == "GET":
        s=Songs.query.filter_by(c_id=id).all()
        return render_template("create_album.html", c_id=id, songs=s)
    album_name=request.form["a_name"]
    asongs=request.form.getlist("song")
    albm=Album(c_no=id,album_name=album_name)
    db.session.add(albm)
    db.session.commit()
    for song in asongs:
        asong=Als(album_id=albm.album_id, song_id=song)
        db.session.add(asong)
    db.session.commit()
    return redirect(f"/redirect/creator/{id}")

@app.route('/<tpes>/search/<int:id>', methods=["POST"])
def c_search(tpes,id):
    search=request.form["search"]
    if tpes =='creator':
        salbum=Album.query.filter(and_(Album.album_name.ilike(f'%{search}%'),Album.c_no==id)).all()
        ssong=Songs.query.filter(and_(Songs.song_name.ilike(f'%{search}%'),Songs.c_id==id)).all()
        srating=Songs.query.filter_by(rating=search, c_id=id).all()    
        myalbm=Album.query.filter_by(c_no=id).all()
        s=Songs.query.filter_by(c_id=id).all()
        return render_template("c_dash.html", myalbm=myalbm, mysongs=s, c=id,sa=salbum,ss=ssong,sr=srating,search=search)
    elif tpes == 'user':
        salbum=Album.query.filter(Album.album_name.ilike(f'%{search}%')).all()
        ssong=Songs.query.filter(Songs.song_name.ilike(f'%{search}%')).all()
        srating=Songs.query.filter_by(rating=search).all()
        play_list=Playlist.query.filter_by(s_no=id).all()
        song=Songs.query.order_by(Songs.rating.desc()).limit(10).all()
        albums=Album.query.limit(10).all()
        return render_template('u_dash.html',u=id,pls=play_list,songs=song,albums=albums,sa=salbum,ss=ssong,sr=srating,search=search)

@app.route("/change_admin/<ch>", methods=["GET","POST"])
def change_admin(ch):
    if request.method=="GET" and ch=="change":
        return render_template("changes_admin.html", Change="Change Admin Details",types=ch)
    elif request.method=="GET" and ch=="register":
        return render_template("changes_admin.html", Change="Register", view="hidden", types=ch)
    uid=request.form["new_id"]
    pswd=request.form["new_pass"]
    if ch=="register":
        if Admin.query.first():
            return render_template("changes_admin.html",types=ch,view="hidden", Change="Register", msg="Admin already exists. Try to change admin details")
        else:
            adm=Admin(id=uid,password=pswd)
            db.session.add(adm)
            db.session.commit()
            return render_template("admin.html", user="admin")
    elif ch=="change":
        oid=request.form["id"]
        opswd=request.form["pass"]
        a,b=Admin.query.filter_by(id=oid).first(),Admin.query.filter_by(password=opswd).first()
        if Admin.query.all()!=[]:
            if a:
                a.id=uid
                a.password=pswd
                db.session.commit()
            elif b:
                b.id=uid
                b.password=pswd
                db.session.commit()
            else:
                return render_template("changes_admin.html", types=ch, Change="Change Admin Details", msg="User ID or Password is incorrect")
            return render_template("admin.html", user="admin")
        else:
            return render_template("changes_admin.html", types=ch, Change="Change Admin details", msg="First register any admin")

@app.route('/admin')
def admin():
    s=Songs.query.all()
    f=list(filter(lambda x: x.flag==1, s))
    c=Creator.query.all()
    u=Users.query.all()
    a=Album.query.all()
    
    x=list(map(lambda x: x.id,c))
    y=list(map(lambda x: Album.query.filter_by(c_no=x.c_id).count(),c))
    fig, ax = plt.subplots() 
    ax.plot(x,y,label='Alubm - Creator Plot',marker='o',linestyle='--')
    ax.set_xlabel("Creator id")
    ax.set_ylabel("Number of Albums created")
    plt.savefig('static/plot.png')
    plt.close(fig)
    
    return render_template("admin_dash.html", songs=s, creators=c, users=u, albums=a, flag=f)


@app.route('/admin/c_detail', methods=["GET","POST"])
def c_details():
    c=Creator.query.all()
    if request.method=="POST":
        search=request.form["search"]
        sc=Creator.query.filter(Creator.name.ilike(f'%{search}%')).all()
        return render_template('creators_detail.html', creator=c, search=search, sc=sc)
    return render_template('creators_detail.html', creator=c)

@app.route('/block/<id>')
def block(id):
    c=Creator.query.filter_by(c_id=id).first()
    c.blacklist=1
    db.session.commit()
    return redirect(url_for('c_details'))

@app.route('/unblock/<id>')
def unblock(id):
    c=Creator.query.filter_by(c_id=id).first()
    c.blacklist=0
    db.session.commit()
    return redirect(url_for('c_details'))

@app.route('/s_update/<int:sid>/<int:cid>', methods=["POST"])
def s_update(sid,cid):
    response=request.form["update"]
    song=Songs.query.filter_by(song_id=sid).first()
    if response=='block':
        creator=Creator.query.filter_by(c_id=cid).first()
        creator.flaged+=1
        file=join(app.config["UPLOAD_FOLDER"],(song.song_name + ".mp3"))
        if exists(file):
            remove(file)
        db.session.delete(song)
        for s in Als.query.filter_by(song_id=sid).all():
            db.session.delete(s)
        for s in Pls.query.filter_by(song_id=sid).all():
            db.session.delete(s)
        db.session.commit()
    song.flag=0
    db.session.commit()
    return redirect(url_for('admin'))

@app.template_filter('avg')
def avg(s):
    sv=0
    s=list(filter(lambda x: x.rating!=0,s))
    for val in s:
        sv+=val.rating
    try:
        res=sv/len(s)
    except:
        res=0
    return int(res*100)/100

@app.template_filter('nsongs')
def nsongs(i):
    s=Songs.query.filter_by(c_id=i).count()
    return s

@app.template_filter('nalbums')
def nalbums(i):
    a=Album.query.filter_by(c_no=i).count()
    return a

@app.template_filter('decency')
def decency(i):
    s=Songs.query.filter_by(c_id=i).count()
    f=Creator.query.filter_by(c_id=i).first().flaged
    try:
        r=int(s/(s+f)*100)
    except:
        r='--'
    return r

@app.template_filter('integer')
def integer(i):
    r=format(i,".2f")
    return float(r)
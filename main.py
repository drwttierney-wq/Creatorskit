import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import os
from openai import OpenAI
from flask_socketio import SocketIO, emit, join_room
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///creatorskit.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text)
    followers = db.relationship('Follow', foreign_keys='Follow.followed_id', backref='followed', lazy=True)
    following = db.relationship('Follow', foreign_keys='Follow.follower_id', backref='follower', lazy=True)

    def is_following(self, user):
        return Follow.query.filter_by(follower_id=self.id, followed_id=user.id).first() is not None

class SavedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    tool_name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text)
    result = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    image = db.Column(db.String(200))
    attached_idea = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    likes = db.relationship('Like', backref='post', lazy=True)
    comments = db.relationship('Comment', backref='post', lazy=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    content = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Follow(db.Model):
    follower_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    image = db.Column(db.String(200))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    read = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class LiveRoom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200))
    active = db.Column(db.Boolean, default=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def ai_generate(platform: str, tool: str, prompt: str) -> str:
    # (the full system_prompts dict from previous versions — paste the long one here)
    # Omit for brevity in this response, but in your file, use the full one with all platforms

    full_prompt = system_prompts.get(platform, {}).get(tool, "Generate helpful content.")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": prompt or "Generate now."}
        ],
        temperature=0.9,
        max_tokens=1000
    )
    return response.choices[0].message.content.strip()

# Routes (full set with all features)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('register'))
        user = User(username=username, password=generate_password_hash(request.form['password']))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/profile')
@login_required
def profile():
    items = SavedItem.query.filter_by(user_id=current_user.id).order_by(SavedItem.timestamp.desc()).all()
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).all()
    return render_template('profile.html', items=items, posts=posts)

@app.route('/profile/<int:user_id>')
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    posts = Post.query.filter_by(user_id=user_id).order_by(Post.timestamp.desc()).all()
    is_following = current_user.is_following(user)
    return render_template('user_profile.html', user=user, posts=posts, is_following=is_following)

@app.route('/platform/<platform>')
@login_required
def platform_page(platform):
    valid_platforms = ['tiktok','youtube','instagram','twitter','facebook','snapchat','linkedin','pinterest','threads','reddit','twitch','onlyfans','discord','monetization']
    if platform not in valid_platforms:
        flash('Platform not found')
        return redirect(url_for('dashboard'))
    return render_template(f'{platform}.html')

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    data = request.get_json()
    platform = data['platform']
    tool = data['tool']
    prompt = data.get('prompt', '')
    result = ai_generate(platform, tool, prompt)

    saved = SavedItem(user_id=current_user.id, platform=platform, tool_name=tool, prompt=prompt, result=result)
    db.session.add(saved)
    db.session.commit()

    return jsonify({'result': result})

@app.route('/community')
@login_required
def community():
    return render_template('community.html')

@app.route('/feed')
@login_required
def feed():
    followed = [f.followed_id for f in current_user.following]
    followed.append(current_user.id)
    posts = Post.query.filter(Post.user_id.in_(followed)).order_by(Post.timestamp.desc()).all()
    return render_template('feed.html', posts=posts)

@app.route('/post', methods=['GET', 'POST'])
@login_required
def post():
    if request.method == 'POST':
        content = request.form['content']
        attached = request.form.get('attached_idea', '')
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename
        new_post = Post(user_id=current_user.id, content=content, image=image, attached_idea=attached)
        db.session.add(new_post)
        db.session.commit()
        emit('new_post', {'post_id': new_post.id}, broadcast=True)  # Real-time update
        return redirect(url_for('feed'))
    saved = SavedItem.query.filter_by(user_id=current_user.id).all()
    return render_template('post.html', saved=saved)

@app.route('/like/<int:post_id>')
@login_required
def like(post_id):
    post = Post.query.get_or_404(post_id)
    like = Like.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    if like:
        db.session.delete(like)
    else:
        db.session.add(Like(user_id=current_user.id, post_id=post_id))
        db.session.add(Notification(user_id=post.user_id, content=f"{current_user.username} liked your post"))
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/comment/<int:post_id>', methods=['POST'])
@login_required
def comment(post_id):
    post = Post.query.get_or_404(post_id)
    content = request.form['content']
    comment = Comment(user_id=current_user.id, post_id=post_id, content=content)
    db.session.add(comment)
    db.session.add(Notification(user_id=post.user_id, content=f"{current_user.username} commented on your post"))
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/follow/<int:user_id>')
@login_required
def follow(user_id):
    user = User.query.get_or_404(user_id)
    if user_id == current_user.id:
        return redirect(url_for('feed'))
    follow = Follow.query.filter_by(follower_id=current_user.id, followed_id=user_id).first()
    if follow:
        db.session.delete(follow)
    else:
        db.session.add(Follow(follower_id=current_user.id, followed_id=user_id))
        db.session.add(Notification(user_id=user_id, content=f"{current_user.username} followed you"))
    db.session.commit()
    return redirect(url_for('feed'))

@app.route('/messages')
@login_required
def messages():
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('messages_inbox.html', users=users)

@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat(user_id):
    other_user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        content = request.form.get('content')
        image = None
        if 'image' in request.files:
            file = request.files['image']
            if file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image = filename
        msg = Message(sender_id=current_user.id, receiver_id=user_id, content=content, image=image)
        db.session.add(msg)
        db.session.commit()
        emit('new_private_message', {'sender': current_user.username, 'content': content, 'image': image, 'timestamp': msg.timestamp.strftime('%H:%M')}, room=f"user_{user_id}")
        db.session.add(Notification(user_id=user_id, content=f"{current_user.username} sent you a message"))
        db.session.commit()
        return redirect(url_for('chat', user_id=user_id))
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id = user_id)) |
        ((Message.sender_id == user_id) & (Message.receiver_id = current_user.id))
    ).order_by(Message.timestamp.asc()).all()
    return render_template('chat.html', other_user=other_user, messages=messages)

@app.route('/notifications')
@login_required
def notifications():
    notifs = Notification.query.filter_by(user_id=current_user.id, read=False).order_by(Notification.timestamp.desc()).all()
    for n in notifs:
        n.read = True
    db.session.commit()
    return render_template('notifications.html', notifs=notifs)

@app.route('/live')
@login_required
def live():
    rooms = LiveRoom.query.filter_by(active=True).all()
    return render_template('live_rooms.html', rooms=rooms)

@app.route('/live/create', methods=['POST'])
@login_required
def create_live():
    title = request.form['title']
    room = LiveRoom(host_id=current_user.id, title=title)
    db.session.add(room)
    db.session.commit()
    return redirect(url_for('live_room', room_id=room.id))

@app.route('/live/<int:room_id>')
@login_required
def live_room(room_id):
    room = LiveRoom.query.get_or_404(room_id)
    return render_template('live_room.html', room=room)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@socketio.on('join_community')
def on_join():
    join_room('community')
    emit('status', {'msg': f'{current_user.username} joined'}, room='community')

@socketio.on('send_message')
def on_message(data):
    emit('new_message', {'user': current_user.username, 'msg': data['msg']}, room='community')

@socketio.on('join_private')
def on_join_private(data):
    room = f"chat_{sorted([current_user.id, data['user_id']]) [0]}_{sorted([current_user.id, data['user_id']])[1]}"
    join_room(room)

@socketio.on('send_private_message')
def on_private_message(data):
    room = f"chat_{sorted([current_user.id, data['receiver_id']])[0]}_{sorted([current_user.id, data['receiver_id']])[1]}"
    emit('new_private_message', {'sender': current_user.username, 'content': data['content']}, room=room)

@socketio.on('join_live')
def on_join_live(data):
    room = f"live_{data['room_id']}"
    join_room(room)
    emit('status', {'msg': f'{current_user.username} joined the live'}, room=room)

@socketio.on('send_live_message')
def on_live_message(data):
    room = f"live_{data['room_id']}"
    emit('new_live_message', {'user': current_user.username, 'msg': data['msg']}, room=room)

@socketio.on('new_post')
def on_new_post(data):
    emit('new_post', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

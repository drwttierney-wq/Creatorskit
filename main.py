from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
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

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app)

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class SavedItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)
    tool_name = db.Column(db.String(100), nullable=False)
    prompt = db.Column(db.Text)
    result = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def ai_generate(platform: str, tool: str, prompt: str) -> str:
    system_prompts = {
        "tiktok": {
            "Idea Generator": "Generate a viral TikTok video idea with hook, trend, music, and CTA.",
            "Script Writer": "Write a full TikTok script with lines, overlays, transitions.",
            "Hashtag Generator": "Give 15 trending + niche hashtags.",
            "Caption Creator": "Write 5 engaging captions with emojis.",
            "Trend Analyzer": "Explain current trends and how to use them.",
            "Sound Finder": "Suggest 5 viral sounds.",
            "Thumbnail Idea": "Describe 5 eye-catching thumbnails."
        },
        "youtube": {
            "Title Generator": "10 SEO-optimized YouTube titles.",
            "Description Writer": "Full SEO description with timestamps & links.",
            "Script Writer": "Complete video script.",
            "Thumbnail Prompt": "Detailed Midjourney thumbnail prompts.",
            "Tag Generator": "15 high-volume tags.",
            "Idea Brainstorm": "5 unique video ideas.",
            "SEO Analyzer": "SEO improvement suggestions."
        },
        "instagram": {
            "Caption Creator": "5 aesthetic captions.",
            "Hashtag Set": "30 targeted hashtags.",
            "Reels Idea": "Trending Reels concept.",
            "Story Ideas": "10 Story ideas.",
            "Bio Optimizer": "3 catchy bios.",
            "Carousel Post": "10-slide carousel plan.",
            "Highlight Covers": "Theme & text suggestions."
        },
        "twitter": {
            "Thread Writer": "10-tweet viral thread.",
            "Tweet Generator": "5 punchy tweets.",
            "Reply Ideas": "5 engagement replies.",
            "Poll Creator": "Poll + 4 options.",
            "Quote Tweet": "Quote response.",
            "Viral Hook": "5 opening hooks."
        },
        "facebook": {
            "Post Caption": "Engaging post copy.",
            "Ad Copy": "Ad headline + body + CTA.",
            "Group Post": "Community post.",
            "Event Description": "Event text.",
            "Reels Idea": "Facebook Reels concept."
        },
        "snapchat": {
            "Story Idea Generator": "5 Story ideas with filters.",
            "Spotlight Video Concept": "Viral Spotlight idea.",
            "AR Lens Prompt": "Lens Studio prompt.",
            "Caption & Sticker Ideas": "10 captions + stickers.",
            "Trend Challenge": "Current trend challenge.",
            "Bitmoji Outfit Suggestion": "5 outfits.",
            "Memories Compilation": "Compilation plan."
        },
        "linkedin": {
            "Post Generator": "Professional post with CTA.",
            "Carousel Planner": "10-slide carousel.",
            "Thought Leadership Article": "800-1200 word article.",
            "Comment Reply Ideas": "5 insightful replies.",
            "Headline Optimizer": "10 headlines.",
            "Poll Creator": "Professional poll.",
            "Bio Refresher": "3 optimized bios."
        },
        "pinterest": {
            "Pin Idea Generator": "5 pin ideas + visuals.",
            "Pin Title Creator": "10 SEO titles.",
            "Description Writer": "Engaging description.",
            "Hashtag Set": "20 hashtags.",
            "Board Strategy": "Board organization tips.",
            "Trend Analyzer": "Current trends.",
            "Rich Pin Optimizer": "Idea/Product/Video pin text."
        },
        "threads": {
            "Thread Starter": "Strong opening post.",
            "Full Thread Builder": "5-10 post thread.",
            "Reply Generator": "5 replies.",
            "Poll Idea": "Poll + options.",
            "Quote Post": "Quote response.",
            "Viral Hook": "10 hooks.",
            "Conversation Extender": "Follow-up posts."
        },
        "reddit": {
            "Post Title Generator": "10 upvote titles.",
            "Post Body Writer": "Full post body.",
            "Comment Ideas": "5 comments.",
            "AMA Planner": "AMA outline.",
            "Subreddit Fit": "Best subreddits.",
            "Meme Caption": "Funny captions.",
            "Self-Promotion Text": "Rule-compliant promo."
        },
        "twitch": {
            "Stream Title Generator": "10 catchy titles.",
            "Schedule Planner": "Weekly stream schedule.",
            "Overlay Ideas": "Stream overlay concepts.",
            "Emote Suggestions": "Emote ideas.",
            "Clip Highlight Script": "Clip narration.",
            "Panel Text": "About/Donate panels.",
            "Raid Message": "Raid/shoutout messages."
        },
        "onlyfans": {
            "Post Caption": "Engaging caption ideas.",
            "Promo Tweet": "Twitter promo text.",
            "PPV Message": "Pay-per-view tease.",
            "Welcome Message": "New subscriber DM.",
            "Content Calendar": "Weekly posting plan.",
            "Tip Menu": "Tip menu suggestions.",
            "Story Teaser": "Story/Status teasers."
        },
        "discord": {
            "Server Intro": "Welcome channel text.",
            "Role Suggestions": "Role ideas & permissions.",
            "Channel Structure": "Channel layout plan.",
            "Bot Commands": "Fun/useful bot ideas.",
            "Event Announcement": "Event post.",
            "Rules Text": "Clear server rules.",
            "Emoji Pack": "Custom emoji concepts."
        },
        "monetization": {
            "Revenue Strategy Planner": "Create a full 30-day monetization plan with multiple income streams.",
            "Pricing Calculator": "Suggest optimal pricing for products/services based on niche and audience.",
            "Sponsorship Pitch Script": "Professional sponsorship pitch email/DM script.",
            "Product Idea Generator": "5 high-demand product ideas for your niche.",
            "Upsell & Funnel Builder": "Design a sales funnel with offers.",
            "Affiliate Program Suggestions": "Top affiliate programs + promo ideas.",
            "Tax & Finance Tips": "Creator-specific tax and finance advice for 2025."
        }
    }

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
    return render_template('profile.html', items=items)

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

@socketio.on('join_community')
def on_join():
    join_room('community')
    emit('status', {'msg': f'{current_user.username} joined'}, room='community')

@socketio.on('send_message')
def on_message(data):
    emit('new_message', {'user': current_user.username, 'msg': data['msg']}, room='community')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)

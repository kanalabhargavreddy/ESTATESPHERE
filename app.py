from flask import Flask, request, render_template, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

# Flask App Configuration
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///real_estate.db'  # Single database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Models
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    images = db.Column(db.Text, nullable=True)

# Initialize the database
def create_tables():
    with app.app_context():
        db.create_all()

# Call the function manually
create_tables()


# Routes
@app.route('/')
def home():
    return render_template('HomePage.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            flash('Passwords do not match!')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('Email address already exists!')
            return redirect(url_for('register'))

        new_user = User(
            email=email,
            password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again.')
            return redirect(url_for('login'))

        session['user_id'] = user.id
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!')
    return redirect(url_for('home'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        flash('Please login first.')
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
        flash('Please login first.')
        return redirect(url_for('login'))

    return render_template('dashboard.html', user=user)

@app.route('/buyers')
def buyers():
    query = Property.query

    # Get filter parameters
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    location = request.args.get('location')

    # Apply filters
    if min_price is not None:
        query = query.filter(Property.price >= min_price)
    if max_price is not None:
        query = query.filter(Property.price <= max_price)
    if location:
        query = query.filter(Property.location == location)

    # Get unique locations for the dropdown
    locations = db.session.query(Property.location).distinct().all()
    locations = [location[0] for location in locations]

    properties = query.all()
    return render_template('Buyers.html', properties=properties, locations=locations)

@app.route('/sellers', methods=['GET', 'POST'])
def sellers():
    if request.method == 'POST':
        title = request.form['title']
        location = request.form['location']
        description = request.form['description']
        price = request.form['price']
        phone = request.form['phone']
        images = request.files.getlist('images')

        image_paths = []
        for image in images:
            if image:
                filename = secure_filename(image.filename)
                relative_path = f'uploads/{filename}'
                image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(image_path)
                image_paths.append(relative_path)

        new_property = Property(
            title=title,
            location=location,
            description=description,
            price=float(price),
            phone=phone,
            images=','.join(image_paths)
        )
        db.session.add(new_property)
        db.session.commit()
        return redirect(url_for('buyers'))

    return render_template('For Sellers.html')

@app.route('/aboutus')
def aboutus():
    return render_template('About Us.html')

@app.route('/contactus')
def contactus():
    return render_template('Contact Us.html')
@app.route('/debug/users')
def debug_users():
    if app.debug:
        users=User.query.all()
        return render_template('debug_users.html',users=users)
    return "Not available in production",403

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize the app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:pass@localhost/libraryDbase'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database and Marshmallow
db = SQLAlchemy(app)
ma = Marshmallow(app)

# User Model
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_number = db.Column(db.String(15))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    user_type = db.Column(db.String(50), nullable=False)  # 'student' or 'staff'
    fine_due = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, name, contact_number, email, password, user_type):
        self.name = name
        self.contact_number = contact_number
        self.email = email
        self.password = password
        self.user_type = user_type

# Book Model
class Book(db.Model):
    book_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    edition = db.Column(db.String(50))
    author = db.Column(db.String(100), nullable=False)
    total_copies = db.Column(db.Integer, nullable=False)
    available_copies = db.Column(db.Integer, nullable=False)
    cost = db.Column(db.Numeric(10, 2))
    source = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Transaction Record Model
class TransactionRecord(db.Model):
    transaction_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.book_id'), nullable=False)
    borrow_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime)
    is_returned = db.Column(db.Boolean, default=False)
    overdue_days = db.Column(db.Integer, default=0)
    fine_imposed = db.Column(db.Numeric(10, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# User Schema
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

# Book Schema
class BookSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Book

# Transaction Record Schema
class TransactionRecordSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRecord

# Create User (POST)
@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    name = data.get('name')
    contact_number = data.get('contact_number')
    email = data.get('email')
    password = generate_password_hash(data.get('password'))
    user_type = data.get('user_type')

    new_user = User(name=name, contact_number=contact_number, email=email, password=password, user_type=user_type)
    
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'User added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# Get All Users (GET)
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    user_schema = UserSchema(many=True)
    return jsonify(user_schema.dump(users))

# Get Single User by ID (GET)
@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user:
        user_schema = UserSchema()
        return jsonify(user_schema.dump(user))
    return jsonify({'message': 'User not found'}), 404

# Update User (PUT)
@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get(user_id)
    if user:
        data = request.json
        user.name = data.get('name', user.name)
        user.contact_number = data.get('contact_number', user.contact_number)
        user.email = data.get('email', user.email)
        user.password = generate_password_hash(data.get('password', user.password))
        user.user_type = data.get('user_type', user.user_type)
        
        try:
            db.session.commit()
            return jsonify({'message': 'User updated successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400
    return jsonify({'message': 'User not found'}), 404

# Delete User (DELETE)
@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        try:
            db.session.delete(user)
            db.session.commit()
            return jsonify({'message': 'User deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400
    return jsonify({'message': 'User not found'}), 404

# Create Book (POST)
@app.route('/books', methods=['POST'])
def add_book():
    data = request.json
    title = data.get('title')
    edition = data.get('edition')
    author = data.get('author')
    total_copies = data.get('total_copies')
    available_copies = data.get('available_copies')
    cost = data.get('cost')
    source = data.get('source')

    new_book = Book(title=title, edition=edition, author=author, total_copies=total_copies, available_copies=available_copies, cost=cost, source=source)

    try:
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'message': 'Book added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 400

# Get All Books (GET)
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    book_schema = BookSchema(many=True)
    return jsonify(book_schema.dump(books))

# Get Single Book by ID (GET)
@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if book:
        book_schema = BookSchema()
        return jsonify(book_schema.dump(book))
    return jsonify({'message': 'Book not found'}), 404
@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if book:
        try:
            db.session.delete(book)
            db.session.commit()
            return jsonify({'message': 'Book deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400
    return jsonify({'message': 'Book not found'}), 404

# Create Transaction Record (POST)
@app.route('/transactions', methods=['POST'])
def create_transaction():
    data = request.json
    user_id = data.get('user_id')
    book_id = data.get('book_id')

    # Check if user is allowed to borrow books (staff cannot borrow)
    user = User.query.get(user_id)
    if user and user.user_type == 'staff':
        return jsonify({'message': 'Staff cannot borrow books'}), 400

    # Check if the book is available
    book = Book.query.get(book_id)
    if book and book.available_copies > 0:
        new_transaction = TransactionRecord(user_id=user_id, book_id=book_id)
        book.available_copies -= 1  # Decrement available copies

        try:
            db.session.add(new_transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction recorded successfully'}), 201
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400
    return jsonify({'message': 'Book not available'}), 400

# Get All Transactions (GET)
@app.route('/transactions', methods=['GET'])
def get_transactions():
    transactions = TransactionRecord.query.all()
    transaction_schema = TransactionRecordSchema(many=True)
    return jsonify(transaction_schema.dump(transactions))



# Return Book (PUT)
@app.route('/transactions/<int:transaction_id>/return', methods=['PUT'])
def return_book(transaction_id):
    transaction = TransactionRecord.query.get(transaction_id)
    if transaction and not transaction.is_returned:
        transaction.is_returned = True
        transaction.return_date = datetime.utcnow()
        
        # Calculate overdue fine
        if transaction.user.user_type == 'student':
            overdue_days = (datetime.utcnow() - transaction.borrow_date).days - 15
            if overdue_days > 0:
                transaction.fine_imposed = overdue_days * 5
                transaction.user.fine_due += transaction.fine_imposed

        # Increment the book's available copies
        book = Book.query.get(transaction.book_id)
        if book:
            book.available_copies += 1

        try:
            db.session.commit()
            return jsonify({'message': 'Book returned successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400
    return jsonify({'message': 'Transaction not found or already returned'}), 404

@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    transaction = TransactionRecord.query.get(transaction_id)
    if transaction:
        try:
            db.session.delete(transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction deleted successfully'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'message': str(e)}), 400
    return jsonify({'message': 'Transaction not found'}), 404


if __name__ == '__main__':
    # Initialize the database tables within an app context
    with app.app_context():
       db.create_all()  # Create tables if they don't exist
  # Create tables if they don't exist
    app.run(debug=True)

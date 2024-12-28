from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

# Initialize the app
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'TheSecretKey' 
jwt = JWTManager(app)

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
        load_instance = True

# Book Schema
class BookSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Book

# Transaction Record Schema
class TransactionRecordSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = TransactionRecord

# Login route (JWT token generation)
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password, password):
        # Generate JWT token
        access_token = create_access_token(identity=str({'user_id': user.user_id, 'user_type': user.user_type}))
        return jsonify({'message': 'Login successful', 'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# Create User (POST)
@app.route('/users', methods=['POST'])
def add_user():
    data = request.json
    
    name = data.get('name')
    contact_number = data.get('contact_number')
    email = data.get('email')
    password = data.get('password')
    user_type = data.get('user_type')
    
    # Validate input data
    if not all([name, contact_number, email, password, user_type]):
        return jsonify({'message': 'Error: Missing required fields.'}), 400
    
    try:
        # Hash the password
        hashed_password = generate_password_hash(password)
        
        # Create new user object
        new_user = User(
            name=name,
            contact_number=contact_number,
            email=email,
            password=hashed_password,
            user_type=user_type
        )
        
        # Add and commit to the database
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'User added successfully.'}), 201
    
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error: Failed to add user. Please try again.'}), 400

# Get All Users (GET)
@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    try:
        # Fetch all users from the database
        users = User.query.all()
        
        # Serialize users using UserSchema
        user_schema = UserSchema(many=True)
        serialized_users = user_schema.dump(users)
        
        return jsonify({'message': 'Users retrieved successfully.', 'data': serialized_users}), 200
    except Exception:
        return jsonify({'message': 'Error: Failed to retrieve users. Please try again later.'}), 500


# Get Single User by ID (GET)
@app.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    try:
        # Fetch the user by ID
        user = User.query.get(user_id)
        
        if user:
            # Serialize the user data
            user_schema = UserSchema()
            serialized_user = user_schema.dump(user)
            
            return jsonify({'message': 'User retrieved successfully.', 'data': serialized_user}), 200
        
        return jsonify({'message': 'Error: User not found.'}), 404
    except Exception:
        return jsonify({'message': 'Error: Failed to retrieve user. Please try again later.'}), 500


# Update User (PUT)
@app.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    try:
        # Fetch the user by ID
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'Error: User not found.'}), 404
        
        # Get data from the request
        data = request.json
        
        # Update user attributes, defaulting to existing values if not provided
        user.name = data.get('name', user.name)
        user.contact_number = data.get('contact_number', user.contact_number)
        user.email = data.get('email', user.email)
        user.password = generate_password_hash(data.get('password')) if 'password' in data else user.password
        user.user_type = data.get('user_type', user.user_type)
        
        # Commit changes to the database
        db.session.commit()
        return jsonify({'message': 'User updated successfully.'}), 200
    
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error: Failed to update user. Please try again later.'}), 500

# Delete User (DELETE)
@app.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    try:
        # Fetch the user by ID
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'Error: User not found.'}), 404
        
        # Proceed to delete the user
        db.session.delete(user)
        db.session.commit()
        return jsonify({'message': 'User deleted successfully.'}), 200

    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error: Could not process the request. Please try again later.'}), 500


# Create Book (POST)
@app.route('/books', methods=['POST'])
@jwt_required()
def add_book():
    data = request.json
    title = data.get('title')
    edition = data.get('edition')
    author = data.get('author')
    total_copies = data.get('total_copies')
    available_copies = data.get('available_copies')
    cost = data.get('cost')
    source = data.get('source')

    # Create a new book entry
    new_book = Book(title=title, edition=edition, author=author, total_copies=total_copies, available_copies=available_copies, cost=cost, source=source)

    try:
        # Attempt to add the new book to the database
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'message': 'Book added successfully.'}), 201

    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error: Could not add book. Please try again later.'}), 500

# Get All Books (GET)
@app.route('/books', methods=['GET'])
@jwt_required()
def get_books():
    try:
        # Fetch all books from the database
        books = Book.query.all()
        
        # If no books found
        if not books:
            return jsonify({'message': 'No books found.'}), 404

        # Serialize books data
        book_schema = BookSchema(many=True)
        return jsonify(book_schema.dump(books)), 200

    except Exception:
        return jsonify({'message': 'Error: Could not retrieve books. Please try again later.'}), 500

# Get Single Book by ID (GET)
@app.route('/books/<int:book_id>', methods=['GET'])
@jwt_required()
def get_book(book_id):
    try:
        # Fetch the book by its ID
        book = Book.query.get(book_id)
        
        # If the book is found
        if book:
            book_schema = BookSchema()
            return jsonify(book_schema.dump(book)), 200
        
        # If the book is not found
        return jsonify({'message': 'Error: Book not found.'}), 404

    except Exception:
        return jsonify({'message': 'Error: Could not retrieve the book. Please try again later.'}), 500

#Delete the Book
@app.route('/books/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book(book_id):
    try:
        # Fetch the book by its ID
        book = Book.query.get(book_id)
        
        # If the book is found
        if book:
            db.session.delete(book)
            db.session.commit()
            return jsonify({'message': 'Book deleted successfully.'}), 200
        
        # If the book is not found
        return jsonify({'message': 'Error: Book not found.'}), 404

    except Exception:
        db.session.rollback()
        return jsonify({'message': 'Error: Could not process the request. Please try again later.'}), 500

# Create Transaction Record (POST)
@app.route('/transactions', methods=['POST'])
@jwt_required()
def create_transaction():
    try:
        data = request.json
        user_id = data.get('user_id')
        book_id = data.get('book_id')

        # Check if user exists and is allowed to borrow books
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        if user.user_type == 'staff':
            return jsonify({'message': 'Staff cannot borrow books'}), 400

        # Check if the book exists and is available
        book = Book.query.get(book_id)
        if not book:
            return jsonify({'message': 'Book not found'}), 404
        if book.available_copies > 0:
            new_transaction = TransactionRecord(user_id=user_id, book_id=book_id)
            book.available_copies -= 1  # Decrement available copies

            try:
                db.session.add(new_transaction)
                db.session.commit()
                return jsonify({'message': 'Transaction recorded successfully'}), 201
            except Exception as e:
                db.session.rollback()
                return jsonify({'message': 'Error: Could not process the transaction. Please try again later.'}), 500

        return jsonify({'message': 'Book not available'}), 400

    except Exception as e:
        return jsonify({'message': 'Error: Could not process the request. Please try again later.'}), 500

# Get All Transactions (GET)
@app.route('/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    try:
        # Fetch all transactions
        transactions = TransactionRecord.query.all()

        # If transactions exist, return them
        if transactions:
            transaction_schema = TransactionRecordSchema(many=True)
            return jsonify(transaction_schema.dump(transactions)), 200
        
        # If no transactions are found
        return jsonify({'message': 'No transactions found'}), 404

    except Exception:
        return jsonify({'message': 'Error: Could not retrieve the transactions. Please try again later.'}), 500


# Return Book (PUT)
@app.route('/transactions/<int:transaction_id>/return', methods=['PUT'])
@jwt_required()
def return_book(transaction_id):
    try:
        # Fetch the transaction record by ID
        transaction = TransactionRecord.query.get(transaction_id)

        # Check if transaction exists
        if not transaction:
            return jsonify({'message': 'Transaction not found'}), 404

        # Check if the book is already returned
        if transaction.is_returned:
            return jsonify({'message': 'Book has already been returned'}), 400

        # Update the transaction as returned
        transaction.is_returned = True
        transaction.return_date = datetime.utcnow()

        # Increment the book's available copies
        book = Book.query.get(transaction.book_id)
        if book:
            book.available_copies += 1
        else:
            return jsonify({'message': 'Book not found'}), 404

        # Commit the changes to the database
        db.session.commit()
        return jsonify({'message': 'Book returned successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error: Could not process the return. Please try again later.'}), 500

@app.route('/transactions/<int:transaction_id>', methods=['DELETE'])
@jwt_required()
def delete_transaction(transaction_id):
    try:
        transaction = TransactionRecord.query.get(transaction_id)

        # If the transaction exists, proceed to delete
        if transaction:
            db.session.delete(transaction)
            db.session.commit()
            return jsonify({'message': 'Transaction deleted successfully'}), 200

        # If transaction is not found
        return jsonify({'message': 'Transaction not found'}), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Error: Could not delete the transaction. Please try again later.'}), 500


if __name__ == '__main__':
    # Initialize the database tables within an app context
    with app.app_context():
       db.create_all()  # Create tables if they don't exist
    app.run(debug=True)

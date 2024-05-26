from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from models import Budget, SavingGoal, User, db, Transaction, Category
import jwt
import datetime

auth = Blueprint('auth', __name__)

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400
    new_user = User(username=username, password_hash=generate_password_hash(password))
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        access_token = create_access_token(identity=username)
        return jsonify({'token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@auth.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@auth.route('/transactions/add', methods=['POST'])
def add_transaction():
    if not request.is_json:
        return jsonify({"error": "JSON body required"}), 400
    data = request.get_json()
    new_transaction = Transaction(
        user_id=data['user_id'],
        amount=data['amount'],
        type=data['type'],
        category=data['category'],
        date=data.get('date', datetime.datetime.utcnow()),
        description=data.get('description', '')
    )
    db.session.add(new_transaction)
    db.session.commit()
    return jsonify({"message": "Transaction added successfully"}), 201

@auth.route('/transactions', methods=['GET'])
def get_transactions():
    user_id = request.args.get('user_id')
    transactions = Transaction.query.filter_by(user_id=user_id).all()
    transactions_data = [{"amount": t.amount, "type": t.type, "category": t.category, "date": t.date, "description": t.description} for t in transactions]
    return jsonify(transactions_data), 200

@auth.route('/categories/add', methods=['POST'])
def add_category():
    data = request.get_json()
    new_category = Category(name=data['name'], type=data['type'])
    db.session.add(new_category)
    db.session.commit()
    return jsonify({"message": "Category added successfully"}), 201

@auth.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    categories_data = [{"name": c.name, "type": c.type} for c in categories]
    return jsonify(categories_data), 200

@auth.route('/budgets', methods=['GET'])
@jwt_required()
def get_budgets():
    user_id = get_jwt_identity()
    budgets = Budget.query.filter_by(user_id=user_id).all()
    budgets_data = [{
        "category_id": budget.category_id,
        "amount": budget.amount,
        "start_date": budget.start_date.strftime('%Y-%m-%d'),
        "end_date": budget.end_date.strftime('%Y-%m-%d')
    } for budget in budgets]
    return jsonify(budgets_data), 200


@auth.route('/budgets', methods=['POST'])
@jwt_required()
def add_budget():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_budget = Budget(
        category_id=data['category_id'],
        user_id=user_id,
        amount=data['amount'],
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d'),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d')
    )
    db.session.add(new_budget)
    db.session.commit()
    return jsonify({"message": "Budget added successfully"}), 201

@auth.route('/saving_goals', methods=['POST'])
@jwt_required()
def add_saving_goal():
    user_id = get_jwt_identity()
    data = request.get_json()
    new_goal = SavingGoal(
        user_id=user_id,
        target_amount=data['target_amount'],
        current_amount=data.get('current_amount', 0),
        target_date=datetime.strptime(data['target_date'], '%Y-%m-%d'),
        description=data.get('description', '')
    )
    db.session.add(new_goal)
    db.session.commit()
    return jsonify({"message": "Saving goal added successfully"}), 201

@auth.route('/saving_goals', methods=['GET'])
@jwt_required()
def get_saving_goals():
    user_id = get_jwt_identity()
    goals = SavingGoal.query.filter_by(user_id=user_id).all()
    goals_data = [{
        "id": goal.id,
        "target_amount": goal.target_amount,
        "current_amount": goal.current_amount,
        "target_date": goal.target_date.strftime('%Y-%m-%d'),
        "description": goal.description
    } for goal in goals]
    return jsonify(goals_data), 200

@auth.route('/expenses/by_category', methods=['GET'])
@jwt_required()
def expenses_by_category():
    user_id = get_jwt_identity()
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    expenses = db.session.query(
        Transaction.category,
        db.func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'Ausgabe',
        Transaction.date >= start_date,
        Transaction.date <= end_date
    ).group_by(Transaction.category).all()

    result = {expense.category: expense.total_amount for expense in expenses}
    return jsonify(result), 200

@auth.route('/expenses/over_time', methods=['GET'])
@jwt_required()
def expenses_over_time():
    user_id = get_jwt_identity()
    interval = request.args.get('interval', 'monthly')  # Default to monthly

    base_query = db.session.query(
        db.func.date_trunc(interval, Transaction.date).label('period'),
        db.func.sum(Transaction.amount).label('total_amount')
    ).filter(
        Transaction.user_id == user_id,
        Transaction.type == 'Ausgabe'
    ).group_by('period')

    if 'start_date' in request.args and 'end_date' in request.args:
        base_query = base_query.filter(
            Transaction.date >= request.args.get('start_date'),
            Transaction.date <= request.args.get('end_date')
        )

    expenses = base_query.all()
    result = {expense.period.strftime('%Y-%m-%d'): expense.total_amount for expense in expenses}
    return jsonify(result), 200

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Define Task model
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    due_date = db.Column(db.String(200), nullable=False)
    is_overdue = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'task': self.task,
            'due_date': self.due_date,
            'is_overdue': self.is_overdue,
        }

# Create the database and table(s)
with app.app_context():
    db.create_all()

# Function to check and update overdue status
def check_and_update_overdue_tasks():
    tasks = Task.query.all()
    current_time = datetime.now()
    for task in tasks:
        due_date = datetime.fromisoformat(task.due_date)
        if due_date < current_time and not task.is_overdue:
            task.is_overdue = True  # Mark as overdue
    db.session.commit()

@app.route('/')
def index():
    check_and_update_overdue_tasks()  # Ensure overdue tasks are updated
    tasks = Task.query.all()
    tasks_dict = [task.to_dict() for task in tasks]
    return render_template('index.html', tasks=tasks_dict)

@app.route('/tasks', methods=['GET'])
def get_tasks():
    check_and_update_overdue_tasks()  # Ensure overdue tasks are updated
    tasks = Task.query.all()
    return jsonify([task.to_dict() for task in tasks])

@app.route('/tasks', methods=['POST'])
def add_task():
    data = request.json
    due_date = datetime.fromisoformat(data['due_date'])
    is_overdue = due_date < datetime.now()

    task = Task(
        task=data['task'],
        due_date=data['due_date'],
        is_overdue=is_overdue,
    )
    db.session.add(task)
    db.session.commit()

    return jsonify(task.to_dict()), 201

@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'message': 'Task not found'}), 404

    data = request.json
    task.task = data.get('task', task.task)  # Update the task description

    db.session.commit()
    return jsonify(task.to_dict()), 200


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task:
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'}), 200
    return jsonify({'message': 'Task not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


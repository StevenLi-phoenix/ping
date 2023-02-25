import os
import time
from datetime import datetime, timedelta

from flask import Flask, request, jsonify, render_template
import threading
import atexit
import json

import CONFIG

app = Flask(__name__)
if CONFIG.test:
    tasks = {int(i + 12032): 0 for i in range(256)}
else:
    tasks = {i: 0 for i in range(256 * 256)}
errors = []

# Load the task list from disk when the program starts
try:
    with open('tasks.json', 'r') as f:
        tasks = json.load(f)
        tasks = {int(k): v for k, v in tasks.items()}
except FileNotFoundError:
    pass

# Load the error list from disk when the program starts
try:
    with open('errors.json', 'r') as f:
        errors = json.load(f)
except FileNotFoundError:
    pass

# Define a variable to keep track of the number of connections
connections = []


# Define a function to calculate the connection rate
def calculate_rate():
    # Get the current time
    now = datetime.now()
    # Filter the connections made within the last window_size minutes
    recent_connections = [conn for conn in connections if now - conn < timedelta(minutes=CONFIG.window_size)]
    # Calculate the connection rate as connections per minute
    rate = len(recent_connections) / CONFIG.window_size
    # Return the connection rate
    return rate


# Save the task list to disk when the program exits
@atexit.register
def save_list():
    for task_id in tasks.keys():
        if tasks[task_id] == 1:
            tasks[task_id] = 0  # reset task status cuz closing
    with open('tasks.json', 'w') as f:
        json.dump(tasks, f)
    with open('errors.json', 'w') as f:
        json.dump(errors, f)


def reset_task_status(index):
    if tasks[index] == 1:
        tasks[index] = 0
        errors.append({'task_index': index, 'error': 'Task timed out'})


def get_task_status(task_id):
    """Return the status code for the given task ID."""
    if int(task_id) in tasks:
        return tasks[int(task_id)]
    else:
        return None


def save_result(task_id, result):
    ip = int(task_id)
    ip1, ip2 = ip // 256, ip % 256
    filename = os.path.join("ip", str(ip1), str(ip2))
    os.makedirs(os.path.join("ip", str(ip1)), exist_ok=True)
    json.dump(result, open(filename, "w"))


@app.route('/get_task', methods=['GET'])
def get_task():
    for index, status_code in tasks.items():
        if status_code == 0:
            tasks[index] = 1
            timer = threading.Timer(600, reset_task_status, [index])
            timer.start()
            return jsonify({'task_index': index, 'task_status': 1})
    return jsonify({'error': 'No tasks available'})


@app.route('/submit_result', methods=['POST'])
def submit_result():
    connections.append(datetime.now())
    task_index = int(request.json['task_index'])
    result = request.json['result']
    result["time"] = int(time.time())
    if task_index not in tasks.keys():
        error = {'task_index': task_index, 'error': f'Index of {task_index} not found'}
    elif result.get('success') and result.get('result_data') and len(result.get('result_data')) == 65536:
        tasks[task_index] = 2
        # start a new thread for saving returning time
        threading.Thread(target=save_result, args=(task_index, result)).start()
        return jsonify({'success': True})
    elif len(result.get('result_data')) != 65536:
        tasks[task_index] = 3
        error = {'task_index': task_index, 'error': f'length:{len(result.get("result_data"))}'}
    else:
        tasks[task_index] = 3
        error = {'task_index': task_index, 'error': 'Unknown error'}
    errors.append(error)
    return jsonify({'success': False, 'error': error})


@app.route('/add_task', methods=['POST'])
def add_task():
    task_status = request.json.get('task_status', 0)
    task_index = max(tasks.keys()) + 1
    tasks[task_index] = task_status
    return jsonify({'success': True, 'task_index': task_index})


@app.route('/error', methods=['GET'])
def error():
    return jsonify(errors)


@app.route('/errors', methods=['GET'])
def geterrors():
    return render_template("error.html")


@app.route('/get_pending', methods=['GET'])
def get_pending():
    return jsonify({k: v for k, v in tasks.items() if v == 1})


@app.route('/get_latest_task', methods=['GET'])
def get_latest_task():
    latest_index = max(filter(lambda i: tasks[i] == 0, tasks))
    if latest_index is None:
        return jsonify({'error': 'No tasks available'})
    return jsonify({'task_index': latest_index, 'task_status': 0})


@app.route('/get_progress', methods=['GET'])
def get_progress():
    total_tasks = len(tasks)
    completed_tasks = list(tasks.values()).count(2)
    progress = round(completed_tasks / total_tasks * 100, 4) if total_tasks > 0 else 0
    return jsonify({
        'progress': progress,
        'done_tasks': completed_tasks,
        'total_tasks': total_tasks,
        'errors': errors,
        'pending': {k: v for k, v in tasks.items() if v == 1}
    })


@app.route('/rate')
def rate():
    ratec = calculate_rate()
    return f'The current connection rate is {ratec:.2f} connections per minute.'


@app.route('/')
def index():
    """Display the task status page."""
    return render_template('status.html', errors=errors)


@app.route('/list')
def indexBlocks():
    """Display the task status page."""
    return render_template('list.html', tasks=tasks, errors=errors)


@app.route('/details/<int:task_id>')
def details(task_id):
    """Display the details for a specific task."""
    status_code = get_task_status(int(task_id))
    if status_code is None:
        return f"Task {task_id} not found"
    else:
        # todo: if sucess open the saved file and render a 256*256 pixel map for succeed ip address
        return render_template('details.html', task_id=task_id, status_code=status_code)


@app.route('/revise')
def revise():
    task_id, code, force = None, None, False
    try:
        task_id = int(request.args.get('id'))
        code = int(request.args.get('code'))
        if request.args.get('force'):
            force = int(request.args.get('force'))
    except Exception as e:
        return {'success': False, "error": str(e)}
    if not force and tasks.get(task_id) and tasks.get(task_id) == 1:
        return {'success': False, "error": "The task is working"}
    if task_id is not None and code is not None:
        tasks[task_id] = code
        return {'success': True}
    else:
        return {'success': False, "error": "Unknown error"}


@app.route('/error/reset')
def error_reset():
    global errors
    try:
        task_id = int(request.args.get('id'))
        if task_id == -1:
            errors = []
            return {'success': True, "error": "RESET ALL ERRORS"}
        else:
            errors = [item for item in errors if item['task_index'] != task_id]
            return {'success': True}
    except Exception as e:
        return {'success': False, "error": str(e)}


# todo: add an user system to thanks for contributing and calculate the submition time based on their submit likewise
#  34 submits/hour or so

@app.route('/ping')
def online():
    """return the server status return {}"""
    return {}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)

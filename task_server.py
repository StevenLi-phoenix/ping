import os

from flask import Flask, request, jsonify, render_template
import threading
import atexit
import json

app = Flask(__name__)

# todo: auto update when task is done, like auto refresh the webpage but not refreshing the whole webpage
# todo: add failure tracking below the tittle
# todo: add current pending block to display

tasks = {i: 0 for i in range(65535)}
errors = []

# Load the task list from disk when the program starts
try:
    with open('tasks.json') as f:
        tasks = json.load(f)
except FileNotFoundError:
    pass


# Save the task list to disk when the program exits
@atexit.register
def save_task_list():
    with open('tasks.json', 'w') as f:
        json.dump(tasks, f)


def reset_task_status(index):
    if tasks[index] == 1:
        tasks[index] = 0
        errors.append({'task_index': index, 'error': 'Task timed out'})


def get_task_status(task_id):
    """Return the status code for the given task ID."""
    if str(task_id) in tasks:
        return tasks[str(task_id)]
    else:
        return None


def save_result(task_id, result):
    ip = int(task_id)
    ip1, ip2 = ip // 256, ip % 256
    filename = os.path.join("ip", str(ip1), str(ip2))
    os.makedirs(os.path.join("ip", str(ip1)), exist_ok=True)
    with open(filename, "w") as f:
        f.write(str(result))


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
    task_index = request.json['task_index']
    result = request.json['result']
    if result.get('success') and result.get('result_data') and len(result.get('result_data')) == 65536:
        tasks[task_index] = 2
        threading.Thread(target=save_result, args=(task_index, result)).start()
        return jsonify({'success': True})
    else:
        tasks[task_index] = 3
        errors.append({'task_index': task_index, 'error': result.get('error', 'Unknown error')})
        return jsonify({'success': False})


@app.route('/add_task', methods=['POST'])
def add_task():
    task_status = request.json.get('task_status', 0)
    task_index = max(tasks.keys()) + 1
    tasks[task_index] = task_status
    return jsonify({'success': True, 'task_index': task_index})


@app.route('/get_errors', methods=['GET'])
def get_errors():
    return jsonify(errors)


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


@app.route('/')
def index():
    """Display the task status page."""
    return render_template('status.html', tasks=tasks, errors=errors)


@app.route('/list')
def indexBlocks():
    """Display the task status page."""
    return render_template('list.html', tasks=tasks, errors=errors)


@app.route('/details/<int:task_id>')
def details(task_id):
    """Display the details for a specific task."""
    status_code = get_task_status(task_id)
    if status_code is None:
        return f"Task {task_id} not found"
    else:
        return render_template('details.html', task_id=task_id, status_code=status_code)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001)

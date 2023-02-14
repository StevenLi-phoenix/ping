import logging
import requests

logger = logging.getLogger('network')


def get_task(server_url):
    # Get a task from the server
    response = requests.get(f'{server_url}/get_task')
    if response.status_code == 200:
        data = response.json()
        task_index = data['task_index']
        logger.info(f'Got task {task_index}, status: {data["task_status"]}')

        # Simulate task processing by waiting for a random amount of time
        return task_index
    else:
        logger.error(f'Error getting task: {response.json()["error"]}')


def submit_task(server_url, task_index, result_data):
    # Submit the result to the server
    result = {'success': True, 'result_data': result_data}
    response = requests.post(f'{server_url}/submit_result', json={'task_index': task_index, 'result': result})
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            logger.info(f'Result for task {task_index} submitted successfully')
        else:
            logger.error(f'Error submitting result for task {task_index}: {data["error"]}')
    else:
        logger.error(f'Error submitting result for task {task_index}: {response.json()["error"]}')

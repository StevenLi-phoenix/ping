import logging
import requests

logger = logging.getLogger('network')


def get_task(server_url):
    # Get a task from the server
    response = requests.get(f'{server_url}/get_task')
    if response.status_code == 200:
        data = response.json()
        task_index = data.get('task_index')
        if task_index:
            logger.info(f'Got task {task_index}, status: {data["task_status"]}')
            return int(task_index)
        else:
            logger.error(f'Error getting task [{response.content}]')
    else:
        logger.error(f'Error getting task [{response.status_code}]')


def submit_task(server_url, task_index, result_data):
    # Submit the result to the server
    task_index = str(task_index)
    result = {'success': True, 'result_data': result_data}
    response = requests.post(f'{server_url}/submit_result', json={'task_index': task_index, 'result': result})
    if response.status_code == 200:
        data = response.json()
        if data['success']:
            logger.info(f'Result for task {task_index} submitted successfully')
        else:
            logger.error(f'Error submitting result for task {task_index}: {data.get("error")}')
    else:
        logger.error(f'Error submitting result for task {task_index} [{response.status_code}]')


if __name__ == '__main__':
    for i in range(25565):
        server = "http://127.0.0.1:8001"
        index = get_task(server)
        submit_task(server, str(index) if index else str(0), "0"*65536)

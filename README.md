# Task Server Website
This project is a task server website that allows users to participate in a task that involves pinging the entire IPv4 address space using the ICMP protocol. The website provides a convenient and efficient platform for distributing the task to interested users.

## Getting Started
To join the task, users can download the [ping.zip](https://github.com/StevenLi-phoenix/ping/releases/latest/download/ping.zip) file and extract it. Then start running the "main.py" script using sudo privileges. This will enable them to start pinging the entire IPv4 address space and contribute to the completion of the task.

## Features
The website is designed to ensure fair distribution of the task and collation of results in an organized manner. Users can track their progress and see how their contributions are advancing the completion of the task.

## Installation
To get started with the project, you can clone the repository to your local machine:
```bash
https://github.com/StevenLi-phoenix/ping.git
```

## Usage
To start the website, navigate to the project directory and run:
```python
python task_server.py
```
This will start the server on http://0.0.0.0:8001/.

To start the clients, download the main.py file and run:(on mac and linux)
 ```python
 sudo python main.py
 ```

## future updates
In the future, we plan to add a user contribution display on the website. This feature will allow users to see their own contributions as well as the contributions of other users to the task. The display will be updated in real-time to show the progress of the task and how it is being completed by the community.

This feature will help users feel more engaged with the task and provide motivation to continue contributing. It will also allow users to see how their contributions are helping to advance the task and reach its completion faster. We believe that this feature will enhance the overall user experience and make the task server website even more engaging and rewarding for all participants.

We are excited to add this feature to the website and look forward to the positive impact it will have on the task completion process.

## Contributing
If you'd like to contribute to this project, please fork the repository and create a pull request.

## Credits
This project was developed by StevenLi.

## License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

# APIs
APIs for a task server implemented using Flask in Python. Below is the description of each API:

### /get_task [GET]
This API is used to get a task from the task list. It returns a JSON object containing the task index and the status code of the task. The status code can be one of the following:

- 0: The task is available and can be taken by the client.
- 1: The task is currently being processed by another client.
- 2: The task has already been completed.
- 3: An error occurred while processing the task.

If there are no tasks available, the API returns a JSON object with an error message.

### /submit_result [POST]

This API is used by the client to submit the result of a task. It takes a JSON object containing the task index and the result data. If the result data is valid and has a length of 65536, the task status is set to 2, indicating that the task has been completed successfully. If the result data is invalid, the task status is set to 3, indicating that an error occurred while processing the task. The API returns a JSON object with a success flag indicating whether the result was submitted successfully, and an error message if there was an error.

### /add_task [POST]

This API is used by the administrator to add a new task to the task list. It takes a JSON object containing the initial status code of the task, which can be 0 (available) or 1 (in progress). The API returns a JSON object with a success flag indicating whether the task was added successfully, and the index of the new task.

### /error [GET]

This API returns a JSON object containing the list of errors that have occurred while processing the tasks. Each error is represented as a JSON object with the task index and the error message.

### /errors [GET]

This API returns an HTML page displaying the list of errors that have occurred while processing the tasks. Each error is represented as a row in a table, with the task index and the error message.

### /get_pending [GET]

This API returns a JSON object containing the list of tasks that are currently in progress (status code 1).

### /get_latest_task [GET]

This API returns the index and the status code of the latest task that was added to the task list and has not yet been taken by any client. If there are no available tasks, the API returns a JSON object with an error message.

### /get_progress [GET]

This API returns the progress of the task processing as a percentage. The progress is calculated as the number of completed tasks divided by the total number of tasks in the task list, multiplied by 100. If there are no tasks in the task list, the API returns a progress of 0. The API returns a JSON object containing the progress percentage.

### /revise [GET]

This API allows the client to revise the status of a task. The client must provide the id of the task and the new code to update the status of the task. If the task is already being worked on, the API returns an error. The API returns a JSON object with a success key indicating whether the update was successful or not.

### /error/reset [GET]

This API allows the client to reset the error status of a task or all tasks. The client must provide the id of the task to reset the error status. If id is -1, then all error statuses will be reset. The API returns a JSON object with a success key indicating whether the reset was successful or not.

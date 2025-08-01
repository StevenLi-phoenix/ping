# Ping the world
This project is python code that allows users to participate in a task that involves pinging the entire IPv4 address space using the ICMP protocol. Also a task server provides a convenient and efficient platform for distributing the task to interested users.

## Getting Started
To join the task, users can download the [ping.zip](https://github.com/StevenLi-phoenix/ping/releases/latest/download/ping.zip) file and extract it. Then start running the "main.py" script using sudo privileges. This will start getting task from preset task server and start pinging the entire IPv4 address space and contribute to the completion of the task.

## Features
The client is designed to run stably and catch all the error.
The website is designed to ensure distribution of the task and collation of results in an organized manner. Users can track their progress and see how their contributions are advancing the completion of the task.

## Installation
To get started with the project, you can clone the repository to your local machine:
```bash
https://github.com/StevenLi-phoenix/ping.git
```

## Usage
To start the website, navigate to the project directory and run:
```bash
python task_server.py
```
This will start the server on http://0.0.0.0:8001/.

To start the clients, download the main.py file and run:(on mac and linux)
 ```bash
 sudo python main.py
 ```

## [Interactive IPv4 Space Map](https://github.com/StevenLi-phoenix/IPv4SpaceVisualizer)

Explore the IPv4 address space visually with the interactive map viewer:

🔗 [IPv4 Space Visualizer](https://stevenli-phoenix.github.io/IPv4SpaceVisualizer/)

This tool lets you interactively browse the IPv4 address space and better understand the distribution and results of your pinging efforts.



## future updates
In the future, I plan to add a user contribution display on the website. This feature will allow users to see their own contributions as well as the contributions of other users to the task. The display will be updated in real-time to show who contribute to task and which it is being completed by the community.

## Contributing
If you'd like to contribute to this project, please fork the repository and create a pull request.
Most likely this will not be updated after the project finished.

## Credits
This project was developed by StevenLi [#](https://github.com/StevenLi-phoenix)

Credits to python [#](https://github.com/python/cpython/graphs/contributors)

The following are Credits for packages used in code:
- Pillow [#](https://github.com/python-pillow/Pillow/graphs/contributors)
- tqdm [#](https://github.com/tqdm/tqdm/graphs/contributors)
- requests [#](https://github.com/psf/requests/graphs/contributors)
- Flask [#](https://github.com/pallets/flask/graphs/contributors)
- hilbertcurve (not included in main but used) [#](https://github.com/galtay/hilbertcurve/graphs/contributors)
- numpy (not included in main but used) [#](https://github.com/numpy/numpy/graphs/contributors)

## License
This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

## Result
I've been running my computer non-stop for days, 24/7, and spent a lot of money buying clusters online to process a specific task. And finally, after all the hard work and dedication, I got the result I was looking for. I'm pleased to announce that the results are now available for download in the release section. The high-resolution version of the output is available, and it's just what I needed to move forward with my project. All the time, money, and effort that I invested in this project were worth it, and I couldn't be happier with the outcome. It's a great feeling to see my hard work pay off in the end.
<img src="https://github.com/StevenLi-phoenix/ping/releases/download/v2.1/ip_4096.png" alt="picture of ping by 4096x4096"/>

## APIs
APIs for a task server implemented using Flask in Python. Below is the description of each API:

### /get_task [GET]
This API is used to get a task from the task list. It returns a JSON object containing the first task with status code 0, returning task index of the task. The status code can be one of the following:

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

*# read only #*
StevenLi-phoenix/ping

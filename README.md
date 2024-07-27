# architect-techtest

This is a FastAPI project that involves creating endpoints to provision and delete VMs, with all operations saved to a local database including created/updated timestamps.

### Commmand to execute the code

`````bash
(venv) ➜ architect-techtest git:(main) ✗ poetry lock --no-update
(venv) ➜ architect-techtest git:(main) ✗ poetry install
(venv) ➜ architect-techtest git:(main) ✗ poetry shell
(venv) ➜ architect-techtest git:(main) ✗ poetry run pytest

### Ensure the environment variable is set and then run the FastAPI application
````bash
(venv) ➜ architect-techtest git:(main) ✗ uvicorn main:app --reload

**Example**:

````bash
curl -X 'POST' \
  'http://127.0.0.1:8000/token' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=testuser&password=testpassword'

{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciJ9.hOROJV-rUAAGWs029hBpc5Unx-7un4g4-TcQxeTS4N4","token_type":"bearer"}%

```bash
curl -X 'POST' \
  'http://127.0.0.1:8000/vms' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciJ9.hOROJV-rUAAGWs029hBpc5Unx-7un4g4-TcQxeTS4N4' \
  -H 'Content-Type: application/json' \
  -d '{
  "name": "test-vm",
  "cpu_cores": 2,
  "memory": 4096,
  "disk_size": 50,
  "public_ip": "192.168.1.1",
  "labels": ["test"]
}'

{"id":"6c7e3b27-7159-4e0a-9e30-3d44284574cd","name":"test-vm","cpu_cores":2,"memory":4096,"disk_size":50,"public_ip":"192.168.1.1","labels":["test"],"status":"created","created_at":"2024-07-27T00:13:14.596945","updated_at":"2024-07-27T00:13:14.596947"}%



```bash
curl -X 'DELETE' \
  'http://127.0.0.1:8000/vms/6c7e3b27-7159-4e0a-9e30-3d44284574cd' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlciJ9.hOROJV-rUAAGWs029hBpc5Unx-7un4g4-TcQxeTS4N4'

{"id":"6c7e3b27-7159-4e0a-9e30-3d44284574cd","name":"test-vm","cpu_cores":2,"memory":4096,"disk_size":50,"public_ip":"192.168.1.1","labels":[],"status":"deleted","created_at":"2024-07-27T00:13:14.596945","updated_at":"2024-07-27T00:13:14.596947"}%


## Part 1: High-Level Design

Design a platform that will allow end-users to create virtual machines and leverage GPUs.
Create a high-level design, including a diagram.

## Part 2: Technical Implementation

You will implement an API for managing VMs based on the design from Part 1.
This involves creating endpoints to provision and delete VMs, with all operations saved to a local database including created/updated timestamps.

### Requirements

- Python 3.10+

### Task

- **Define the Database Model**: Define the database model for storing VM information.
- **Implement the API Endpoints**: Define the endpoints for creating and deleting VMs.
- **Save VM States**: Save the state of the VMs in the local database.

### Additional Info

An SDK is provided to simulate the provisioning and deletion of VMs on the hypervisor layer; `from sdk import Client`.
It includes methods for authentication, creating VMs, and deleting VMs.
The SDK client's API key is set at the environment level and is not required in requests.
`````

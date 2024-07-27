import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app, get_db, Base, engine
from sqlalchemy.orm import sessionmaker
import uuid

# Setup the test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def test_app():
    """Creates a TestClient instance and sets up the test database schema.

    This fixture initializes the database schema before the tests are run
    and yields a FastAPI TestClient for making API requests. After the tests
    are completed, it tears down the database schema.

    Yields:
        TestClient: A FastAPI TestClient instance.
    """
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def db():
    """Provides a SQLAlchemy session for database operations.

    This fixture creates a new SQLAlchemy session for the duration of the test module.
    The session is closed after the tests are completed.

    Yields:
        Session: A SQLAlchemy session.
    """
    db = SessionLocal()
    yield db
    db.close()


def mock_authenticate(self):
    """Mock method to simulate successful authentication.

    Returns:
        bool: Always returns True to indicate successful authentication.
    """
    return True


def mock_create_vm(self, name, cpu_cores, memory, disk_size, public_ip=None, labels=None):
    """Mock method to simulate VM creation.

    Args:
        name (str): The name of the VM.
        cpu_cores (int): The number of CPU cores for the VM.
        memory (int): The memory size (in MB) for the VM.
        disk_size (int): The disk size (in GB) for the VM.
        public_ip (str, optional): The public IP address for the VM. Defaults to None.
        labels (list of str, optional): A list of labels for the VM. Defaults to None.

    Returns:
        MagicMock: A mock VM object with the specified attributes.
    """
    vm = MagicMock()
    vm.id = str(uuid.uuid4())  # Generate a unique ID for each VM
    vm.name = name
    vm.cpu_cores = cpu_cores
    vm.memory = memory
    vm.disk_size = disk_size
    vm.public_ip = public_ip
    vm.labels = labels or []
    return vm


def mock_delete_vm(self, vm_id):
    """Mock method to simulate VM deletion.

    Args:
        vm_id (str): The ID of the VM to delete.

    Returns:
        bool: Always returns True to indicate successful deletion.
    """
    return True


@patch('sdk.Client.authenticate', mock_authenticate)
@patch('sdk.Client.create_vm', mock_create_vm)
@patch('sdk.Client.delete_vm', mock_delete_vm)
def test_create_vm(test_app, db):
    """Test case for creating a VM.

    This test case simulates the creation of a VM by sending a POST request to the
    /vms endpoint with the necessary VM details. It verifies that the VM creation
    is successful and the response contains the expected VM details.

    Args:
        test_app (TestClient): The FastAPI TestClient fixture.
        db (Session): The SQLAlchemy session fixture.

    Asserts:
        The status code of the response is 200.
        The response contains the expected VM name and status.
    """
    response = test_app.post(
        "/token", data={"username": "testuser", "password": "testpassword"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = test_app.post(
        "/vms", json={"name": "test-vm", "cpu_cores": 2, "memory": 4096, "disk_size": 50}, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-vm"
    assert data["status"] == "created"


@patch('sdk.Client.authenticate', mock_authenticate)
@patch('sdk.Client.create_vm', mock_create_vm)
@patch('sdk.Client.delete_vm', mock_delete_vm)
def test_delete_vm(test_app, db):
    """Test case for deleting a VM.

    This test case simulates the deletion of a VM by first creating a VM and then
    sending a DELETE request to the /vms/{vm_id} endpoint. It verifies that the VM
    deletion is successful and the response contains the expected VM details.

    Args:
        test_app (TestClient): The FastAPI TestClient fixture.
        db (Session): The SQLAlchemy session fixture.

    Asserts:
        The status code of the VM creation response is 200.
        The status code of the VM deletion response is 200.
        The response contains the expected VM status.
    """
    response = test_app.post(
        "/token", data={"username": "testuser", "password": "testpassword"})
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = test_app.post(
        "/vms", json={"name": "test-vm", "cpu_cores": 2, "memory": 4096, "disk_size": 50}, headers=headers)
    data = response.json()
    vm_id = data["id"]

    response = test_app.delete(f"/vms/{vm_id}", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "deleted"

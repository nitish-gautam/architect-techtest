import logging
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, IPvAnyAddress
from typing import List, Optional
from sdk import Client
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
import uvicorn
import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Create a base class for declarative class definitions in SQLAlchemy
Base = declarative_base()


class VM(Base):
    """SQLAlchemy ORM model representing a Virtual Machine (VM).

    Attributes:
        id (str): The unique identifier for the VM.
        name (str): The name of the VM.
        cpu_cores (int): The number of CPU cores allocated to the VM.
        memory (int): The amount of memory (in MB) allocated to the VM.
        disk_size (int): The disk size (in GB) allocated to the VM.
        public_ip (str, optional): The public IP address assigned to the VM.
        status (str): The status of the VM (e.g., created, deleted).
        created_at (datetime): The timestamp when the VM was created.
        updated_at (datetime): The timestamp when the VM was last updated.
    """
    __tablename__ = 'vms'

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    cpu_cores = Column(Integer, nullable=False)
    memory = Column(Integer, nullable=False)
    disk_size = Column(Integer, nullable=False)
    public_ip = Column(String, nullable=True)  # Store as string
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow,
                        onupdate=datetime.datetime.utcnow)


# Database setup
# Create a SQLite engine
engine = create_engine('sqlite:///vms.db')
# Create all tables in the database
Base.metadata.create_all(engine)
# Create a configured "Session" class
Session = sessionmaker(bind=engine)

# Create a FastAPI instance
app = FastAPI()
# Initialize the SDK client
sdk_client = Client(api_key=os.getenv('SDK_API_KEY')
                    )  # Ensure SDK_API_KEY is used
# Define OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
# Load secret key from environment variable, or use a default for development
# Default for development
SECRET_KEY = os.getenv('SECRET_KEY', 'dev_secret_key')
# Define JWT algorithm
ALGORITHM = "HS256"


class VMCreateRequest(BaseModel):
    """Pydantic model representing a request to create a VM.

    Attributes:
        name (str): The name of the VM.
        cpu_cores (int): The number of CPU cores allocated to the VM.
        memory (int): The amount of memory (in MB) allocated to the VM.
        disk_size (int): The disk size (in GB) allocated to the VM.
        public_ip (IPvAnyAddress, optional): The public IP address assigned to the VM.
        labels (List[str], optional): A list of labels assigned to the VM.
    """
    name: str
    cpu_cores: int
    memory: int
    disk_size: int
    public_ip: Optional[IPvAnyAddress] = None
    labels: Optional[List[str]] = None


class VMResponse(BaseModel):
    """Pydantic model representing the response for a VM.

    Attributes:
        id (str): The unique identifier for the VM.
        name (str): The name of the VM.
        cpu_cores (int): The number of CPU cores allocated to the VM.
        memory (int): The amount of memory (in MB) allocated to the VM.
        disk_size (int): The disk size (in GB) allocated to the VM.
        public_ip (Optional[str]): The public IP address assigned to the VM.
        labels (List[str]): A list of labels assigned to the VM.
        status (str): The status of the VM (e.g., created, deleted).
        created_at (datetime): The timestamp when the VM was created.
        updated_at (datetime): The timestamp when the VM was last updated.
    """
    id: str
    name: str
    cpu_cores: int
    memory: int
    disk_size: int
    public_ip: Optional[str]
    labels: List[str]
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime


def get_db():
    """Dependency to provide a SQLAlchemy session to path operation functions.

    Yields:
        Session: A SQLAlchemy session.
    """
    db = Session()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme)):
    """Dependency to get the current user from the JWT token.

    Args:
        token (str): The JWT token provided by the user.

    Returns:
        str: The user ID extracted from the token.

    Raises:
        HTTPException: If the token is invalid or user ID is not found.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return user_id
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Endpoint to get JWT token.

    Args:
        form_data (OAuth2PasswordRequestForm): The form data containing username and password.

    Returns:
        dict: A dictionary containing the access token and token type.
    """
    user_id = form_data.username
    access_token = jwt.encode(
        {"sub": user_id}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/vms", response_model=VMResponse)
def create_vm(request: VMCreateRequest, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Endpoint to create a new VM.

    Args:
        request (VMCreateRequest): The request body containing VM details.
        db (Session): The SQLAlchemy session dependency.
        current_user (str): The current user obtained from the token.

    Returns:
        VMResponse: The created VM object.

    Raises:
        HTTPException: If there is an error creating the VM.
    """
    try:
        sdk_client.authenticate()
        vm = sdk_client.create_vm(
            name=request.name,
            cpu_cores=request.cpu_cores,
            memory=request.memory,
            disk_size=request.disk_size,
            public_ip=str(request.public_ip) if request.public_ip else None,
            labels=request.labels
        )
        new_vm = VM(
            id=vm.id,
            name=vm.name,
            cpu_cores=vm.cpu_cores,
            memory=vm.memory,
            disk_size=vm.disk_size,
            public_ip=str(vm.public_ip) if vm.public_ip else None,
            status='created'
        )

        # Dump values before saving to the database
        logging.info(f"Dump new_vm before save: {new_vm.__dict__}")
        print(f"Dump new_vm before save: {new_vm.__dict__}")

        db.add(new_vm)
        db.commit()
        db.refresh(new_vm)
        logging.info(f"VM created: {new_vm}")

        return VMResponse(
            id=new_vm.id,
            name=new_vm.name,
            cpu_cores=new_vm.cpu_cores,
            memory=new_vm.memory,
            disk_size=new_vm.disk_size,
            public_ip=new_vm.public_ip,
            labels=request.labels if request.labels else [],
            status=new_vm.status,
            created_at=new_vm.created_at,
            updated_at=new_vm.updated_at
        )
    except Exception as e:
        logging.error(f"Error creating VM: {str(e)}")
        print(f"Error creating VM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/vms/{vm_id}", response_model=VMResponse)
def delete_vm(vm_id: str, db: Session = Depends(get_db), current_user: str = Depends(get_current_user)):
    """Endpoint to delete a VM.

    Args:
        vm_id (str): The ID of the VM to delete.
        db (Session): The SQLAlchemy session dependency.
        current_user (str): The current user obtained from the token.

    Returns:
        VMResponse: The deleted VM object.

    Raises:
        HTTPException: If the VM is not found or there is an error deleting the VM.
    """
    try:
        sdk_client.authenticate()
        sdk_client.delete_vm(vm_id)
        vm = db.query(VM).filter(VM.id == vm_id).first()
        if vm is None:
            raise HTTPException(status_code=404, detail="VM not found")

        db.delete(vm)  # Delete the VM record from the database
        db.commit()
        logging.info(f"VM deleted: {vm}")

        return VMResponse(
            id=vm.id,
            name=vm.name,
            cpu_cores=vm.cpu_cores,
            memory=vm.memory,
            disk_size=vm.disk_size,
            public_ip=vm.public_ip,
            labels=[],  # Assuming labels are not needed for the delete response
            status='deleted',  # Indicate the VM was deleted
            created_at=vm.created_at,
            updated_at=vm.updated_at
        )
    except Exception as e:
        logging.error(f"Error deleting VM: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # Run the FastAPI app using Uvicorn server
    uvicorn.run(app, host="0.0.0.0", port=8000)

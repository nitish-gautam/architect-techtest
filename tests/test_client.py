import pytest
from sdk import Client
from sdk.exceptions import AuthenticationError


def test_authenticate__without_api_key():
    client = Client(api_key=None)
    with pytest.raises(AuthenticationError):
        client.authenticate()

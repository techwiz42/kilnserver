import os
import tempfile
import pytest
#import kilnweb2
from kilnweb2 import app, model

@pytest.fixture
def client():

    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client:
        with app.app_context():
            yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

def register(client, username, password, full_name, email_address, phone_number):
    return client.post('/register', 
            data=dict(username=username,
                    password=password,
                    full_name=full_name,
                    email_address=email_address,
                    phone_number=phone_number),
            follow_redirects=True)

def login(client, username, password):
    return client.post('/login',
            data=dict(username=username, password=password),
            follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def test_splash_page(client):
    rv = client.get('/')
    assert rv.status_code == 200

def test_login(client):
    rv = login(client, "TESTY", "PASSWORD")
    assert rv.status_code == 200

def test_registration(client):
    ''' make sure registration works '''
    rv = register(client, "TESTY", "PASSWORD", "TEST USER", "test@foo.bar", "(555) 555-5555")
    assert rv.status_code == 200

def test_show_jobs_unauthorized(client):
    ''' user exists, not yet authorized '''
    register(client, "TESTY", "PASSWORD", "TEST USER", "test@foo.bar", "(555) 555-5555")
    login(client, "TESTY", "PASSWORD")
    rv = client.post("/show_jobs")
    assert rv.status_code == 401

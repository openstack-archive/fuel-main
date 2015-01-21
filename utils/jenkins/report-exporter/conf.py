import os

JENKINS = {
    'url': os.environ.get('JENKINS_URL', 'http://localhost/'),
}

GOOGLE = {
    'user': os.environ.get('GOOGLE_USER'),
    'password': os.environ.get('GOOGLE_PASSWORD'),
    'key': os.environ.get('GOOGLE_KEY'),
}

from flask import Flask
import logging
from logging import Formatter, FileHandler
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(16)

if os.environ['APP_ENVIRONMENT'] == 'development':
    app.config['DEBUG'] = True
    app.config['FLASK_ENV'] = 'development'
else:
    app.config['DEBUG'] = False
    app.config['FLASK_ENV'] = 'production'


if not app.debug:
    file_handler = FileHandler('logs/error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s')
    )
    app.logger.setLevel(logging.WARNING)
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')


from flaskapi import endpoints
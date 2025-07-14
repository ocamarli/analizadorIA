
from dotenv import load_dotenv
import os
load_dotenv()

class Config:
    pass

class DevelopmentConfig(Config):
    DEBUG = False
    MONGO_DATABASE_URI = os.getenv('MONGO_DATABASE_URI')
    MONGO_USERNAME = os.getenv('MONGO_USERNAME', '')
    MONGO_PASSWORD = os.getenv('MONGO_PASSWORD', '')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
class LocalConfig(Config):
    DEBUG = True
    MONGO_DATABASE_URI = 'mongodb://localhost:27017/vikkon'
    MONGO_USERNAME = ''
    MONGO_PASSWORD = ''
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', '')
class DockerConfig(Config):
    DEBUG = True

config = {
    'development': DevelopmentConfig,
    'local': LocalConfig,
    'docker': DockerConfig,
}

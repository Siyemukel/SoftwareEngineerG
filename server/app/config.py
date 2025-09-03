import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'acdd6a4ed3cbaa196149e1fab515d1b56b6f6c43d66f42c8ea2829bf3cbf2bd0')
    DB_PATH = os.environ.get('DB_PATH', os.path.join(BASE_DIR, 'instance', 'database.db'))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
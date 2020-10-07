import os


class Config(object):
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Cjl52289011^@localhost:3306/white_list"
    # SQLALCHEMY_DATABASE_URI = "mysql+pymysql://zguser:123456@10.20.21.83:3306/white_list"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    WHOOSH_BASE = os.path.join(basedir, 'search.db')
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    data_per_page = 10
    UPLOAD_FOLDER = 'upload'
    UPLOAD_PATH = UPLOAD_FOLDER
    BABEL_DEFAULT_LOCALE = 'zh_CN'

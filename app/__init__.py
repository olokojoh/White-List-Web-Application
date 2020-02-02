from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
from flask_login import LoginManager
from flask_admin import Admin, AdminIndexView
from flask_babelex import Babel


app = Flask(__name__)
login = LoginManager(app)
login.login_view = 'login'
bootstrap = Bootstrap(app)
app.config.from_object(Config)
babel = Babel(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
admin = Admin(app, name='后台管理系统', index_view=AdminIndexView(name='主页', template='welcome.html', url='/admin'))


from app import views, models, errors

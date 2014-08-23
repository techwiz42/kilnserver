from flask.ext.sqlalchemy import SQLAlchemy
from kilnserver import app
#from sqlalchemy import create_engine
#from sqlalchemy.orm import scoped_session, sessionmaker
#from sqlalchemy.ext.declarative import declarative_base

db = SQLAlchemy(app)
#engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'], convert_unicode=True)
#db_session = scoped_session(sessionmaker(autocommit=True, autoflush=True, bind=engine))

#Base = declarative_base()
#Base.query = db_session.query_property()

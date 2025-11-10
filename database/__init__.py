from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('mysql+pymysql://root:@localhost/db_trabalho3B')
Session = sessionmaker(bind=engine)
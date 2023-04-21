from models import db
from app import app


# create table in database
db.drop_all()
db.create_all()

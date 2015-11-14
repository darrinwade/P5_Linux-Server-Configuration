
# import the various python and sqlalchemy modules needed for
# proper functioning of the Category application
import sys
import datetime

from sqlalchemy                 import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm             import relationship
from sqlalchemy                 import create_engine

# All classes below will extend Base...
Base = declarative_base()

# Table 'Owner' is used to represent a logged in user of
# the Category application.  The user is authenticated via
# third party authentication so only the basic information
# need be stored in the database regarding him/her.
class Owner(Base):
	__tablename__ = 'owner'

	id    = Column(Integer, primary_key=True)
	name  = Column(String(50), nullable=False)
	email = Column(String(200), nullable=False)
	pic   = Column(String(200))

# Table 'Category' is used to store 'parent type' data in
# the database.  Basic information about the category object
# is stored in the table and there is a foreign key relationship
# association of a record in this table to a record in the
# 'Owner' table.
#
# The table is configured to present data in a simple JSON
# format.
class Category(Base):
	__tablename__ = 'category'

	id       = Column(Integer, primary_key=True)
	name     = Column(String(50), nullable=False)
	desc     = Column(String(200))
	createDt = Column(String(30), default=datetime.datetime.utcnow)
	modifyDt = Column(String(30), default=datetime.datetime.utcnow)
	owner_id = Column(Integer, ForeignKey('owner.id'))
	owner    = relationship('Owner')

	@property
	def serialize(self):
		return {
			'category id' : self.id,
			'name' : self.name,
			'description' : self.desc,
			'create date' : self.createDt,
			'modify date' : self.modifyDt,
			'owner key' : self.owner_id,
		}

# Table 'Item' is used to store 'child' data of a given
# category record in the database.  Basic information
# about the category object is stored in the table and
# there are a foreign  key relationship associations
# of a record in this table to a record in the
# 'Owner' table as well as the 'Category' table.
#
# The table is configured to present data in a simple JSON
# format.
class Item(Base):
	__tablename__ = 'item'

	id          = Column(Integer, primary_key=True)
	name        = Column(String(50), nullable=False)
	desc        = Column(String(200))
	createDt    = Column(String(30), default=datetime.datetime.utcnow)
	modifyDt    = Column(String(30), default=datetime.datetime.utcnow)
	category_id = Column(Integer, ForeignKey('category.id'))
	category    = relationship(Category)
	owner_id    = Column(Integer, ForeignKey('owner.id'))
	owner       = relationship('Owner')

	@property
	def serialize(self):
		return {
			'item id' : self.id,
			'name' : self.name,
			'description' : self.desc,
			'create date' : self.createDt,
			'modify date' : self.modifyDt,
			'category key' : self.category_id,
			'owner key' : self.owner_id,
		}

# Execution of these lines of code will create or connect
# the database and add the tables and columns
engine = create_engine('sqlite:///category.db')
Base.metadata.create_all(engine)
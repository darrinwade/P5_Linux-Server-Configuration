
# import the various python and sqlalchemy modules needed for
# proper functioning of the Category application

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
app = Flask(__name__)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from application_dbsetup import Base, Owner, Category, Item

from flask import session as login_session
import random, string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import datetime

# Read the client secrets created on the Google developer's site and used
# in the user authentication process.
CLIENT_ID = json.loads(open('client_secrets.json', 'r').read()) ['web']['client_id']

# Connect to the category database
engine = create_engine('sqlite:///category.db')

# Create a db session object that allows us to communicate
# with our category database.
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

#------------------------------------------

def addDBRec(objToAdd):
	""" Add a new record to the reference table specified."""
	session.add(objToAdd)
	session.commit()

def deleteDBRec(objToDelete):
	""" Update a record in the reference table specified."""
	session.delete(objToDelete)
	session.commit()

def updateDBRec(objToUpdate):
	""" Delete a record in the reference table specified."""
	session.add(objToUpdate)
	session.commit()

@app.route('/login')
def showLogin():
	""" Show my category application login button."""
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state
	return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
	""" Connect to the Google site for application authentication purposes."""
	if request.args.get('state') != login_session['state']:
		print "request => '%s'" % (request)
		print "request.args.get(state) => '%s'" % ( request.args.get('state'))
		print "login_session[state] => '%s'" % (login_session['state'])
		response = make_response(json.dumps('Invalid state parameter.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])

	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	# Check to see if the user is already logged in
	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['credentials'] = credentials
	login_session['gplus_id']    = gplus_id

	# Get user info
	userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params=params)
	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture']  = data['picture']
	login_session['email']    = data['email']

	print "data['name'] '%s'" % (data['name'])
	print "data['email'] '%s'" % (data['email'])
	print "data['picture'] '%s'" % (data['picture'])
	output = ''
	output += '<h1>Welcome, '

	if 	login_session['username'] =="":
		output += login_session['email']
	else:
		output += login_session['username']

	output += '!</h1>'
	output += '<img src="'
	output += login_session['picture']
	output += ' " style = "width: 300px; height: 300px;border-radius: '
	output += '150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '

	if 	login_session['username'] =="":
		flash("You are now logged using email address key - '%s'" % login_session['email'])
	else:
		flash("You are now logged in as '%s'" % login_session['username'])

	print output
	print "done!"
	return output

@app.route('/gdisconnect')
def gdisconnect():
	""" Log the user out of the system."""

	# Only disconnect a connected user.
	credentials = login_session.get('credentials')
	if credentials is None:
		response = make_response(
			json.dumps('Current user not connected'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	access_token = credentials.access_token
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]

	# If no issues revoking access, return success and remove all the
	# session level values for the context user.
	if result['status'] == '200':
		# Reset the user's sesson.
		del login_session['credentials']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']

		response = make_response(json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response
	else:

		# For whatever reason, the given token was invalid.
		response = make_response(
		    json.dumps('Failed to revoke token for given user.', 400))
		response.headers['Content-Type'] = 'application/json'
		return response

def createUser(login_session):
	""" Create a new user in the Owner table using the
	login information stored in session."""
	newUser = Owner(name=login_session['username'], 
		email=login_session['email'], 
		pic=login_session['picture'])

	addDBRec(newUser)
	user = session.query(Owner).filter_by(email=login_session['email']).one()
	return user.id

def getUserInfo(user_id):
	""" Get the user information currently stored in the database. """
	user = session.query(Owner).filter_by(id=user_id).one()
	return user

def getUserID(email):
	""" Get the id of the user based on his/her email which should be unique. """
	try:
		user = session.query(Owner).filter_by(email=email).one()
		return user.id
	except:
		return None

@app.route('/')
@app.route('/Catalog')
@app.route('/CatalogApp')
def showCategories():
	""" Display the main catalog page using any of the listed routes."""
	lCategories = session.query(Category).order_by(Category.name).all()

	if len(lCategories)==0:
		sMsg = ""
		if 'username' not in login_session:
			sMsg  = "There are currently no categories in the system.  "
			sMsg += "Please log in and create entries as needed."
		else:
			sMsg  = "There are currently no categories in the system.  "
			sMsg += "Please create entries as needed."

		flash(sMsg)

	return render_template('categoriesAll.html', CategoryList=lCategories)

@app.route('/CatalogJSON')
@app.route('/CatalogAppJSON')
def showCategoriesJSON():
	""" Show all category entries in JSON format."""
	lCategories = session.query(Category).all()
	return jsonify(Categories=[category.serialize for category in lCategories])

@app.route('/ShowSingleCategoryJSON/<int:category_id>/')
def showSingleCategoryJSON(category_id):
	""" Show an individual category entry in JSON format."""
	oCategory = session.query(Category).filter_by(id=category_id).first()

	if not oCategory:
		sMsg  = "Invalid category_id value, '%s', used in " % (category_id)
		sMsg += "'ShowSingleCategoryJSON' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))
	else:
		return jsonify(Category=[oCategory.serialize])

@app.route('/CreateCategory/', methods=['GET', 'POST'])
def createCategoryEntry():
	""" Create a new category."""	
	if 'username' not in login_session:
		sMsg  = "You are not authorized to perform this '%s' " % ('create category')
		sMsg += "action because you are not logged in.  You are being redirected to login."
		flash(sMsg)
		return redirect('/login')

	if request.method == 'POST':
		if  request.form['CategoryName'] == "":
			sMsg = "You must have a category name in order to complete the create."
			flash(sMsg)
			return render_template('categoryCreate.html')

		iOwnerID = getUserID(login_session['email'])

		if iOwnerID==None:
			iOwnerID=createUser(login_session)

		sTmpName = request.form['CategoryName']
		oNewCategory  = Category(name=request.form['CategoryName'],
			                     desc=request.form['CategoryDesc'],
			                     owner_id=iOwnerID)
		addDBRec(oNewCategory)
		sMsg = "New category, '%s', created." % (sTmpName)
		flash(sMsg)
		return redirect(url_for('showCategories'))
	else:
		return render_template('categoryCreate.html')

@app.route('/ViewCategory/<int:category_id>/')
def viewCategoryEntry(category_id):
	""" View a category entry."""	
	oViewCategory = session.query(Category).filter_by(id=category_id).first()
	if not oViewCategory:
		sMsg  = "Invalid category_id value, '%s', used in " % (category_id)
		sMsg += "'ViewCategory' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	return render_template('categoryView.html', CategoryToView=oViewCategory)

@app.route('/EditCategory/<int:category_id>/', methods=['GET', 'POST'])
def editCategoryEntry(category_id):
	""" Edit a category entry."""	
	if 'username' not in login_session:
		sMsg  = "You are not authorized to perform this '%s' " % ('edit category')
		sMsg += "action because you are not logged in.  You are being redirected to login."
		flash(sMsg)
		return redirect('/login')

	iSessionUser = getUserID(login_session['email'])
	if iSessionUser==None:
		sMsg  = "Fatal error!!!  Unable to find a matching Owner.id value for "
		sMsg += "unique session email address, '%s' " % (login_session['email'])
		sMsg += "during 'EditCategory' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	oEditCategory = session.query(Category).filter_by(id=category_id).first()
	if not oEditCategory:
		sMsg  = "Invalid category_id value, '%s', used in " % (category_id)
		sMsg += "'EditCategory' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	print "iSessionUser => '%s'" % (iSessionUser)
	print "oEditCategory.owner_id => '%s'" % (oEditCategory.owner_id)
	if oEditCategory.owner_id != iSessionUser:
		sMsg  = "You can not edit category '%s' because you are not " % (oEditCategory.name)
		sMsg += "the owner of it."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	if request.method == 'POST':
		if  request.form['CategoryName'] == "":
			sMsg = "You must have a category name in order to complete the edit."
			flash(sMsg)
			return render_template('categoryEdit.html', CategoryToEdit=oEditCategory)			

		sOrigName = oEditCategory.name
		oEditCategory.name     =  request.form['CategoryName']
		oEditCategory.desc     = request.form['CategoryDesc']
		oEditCategory.modifyDt = datetime.datetime.utcnow()
		updateDBRec(oEditCategory)
		if sOrigName == oEditCategory.name:
			sMsg = "Category, '%s', content edited." % (oEditCategory.name)
		else:
			sMsg = "Category '%s' name changed to '%s'." % (sOrigName, oEditCategory.name)

		flash(sMsg)
		return redirect(url_for('showCategories'))
	else:
		return render_template('categoryEdit.html', CategoryToEdit=oEditCategory)

@app.route('/DeleteCategory/<int:category_id>/', methods=['GET', 'POST'])
def deleteCategoryEntry(category_id):
	""" Delete a category."""		
	if 'username' not in login_session:
		sMsg  = "You are not authorized to perform this '%s' " % ('delete category')
		sMsg += "action because you are not logged in.  You are being redirected to login."
		flash(sMsg)
		return redirect('/login')

	iSessionUser = getUserID(login_session['email'])
	if iSessionUser==None:
		sMsg  = "Fatal error!!!  Unable to find a matching Owner.id value for "
		sMsg += "unique session email address, '%s' " % (login_session['email'])
		sMsg += "during 'DeleteCategory' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	oDeleteCategory = session.query(Category).filter_by(id=category_id).first()

	if not oDeleteCategory:
		sMsg  = "Invalid category_id value, '%s', used in " % (category_id)
		sMsg += "'DeleteCategory' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	if oDeleteCategory.owner_id != iSessionUser:
		sMsg  = "You can not delete category '%s' because you are not " % (oDeleteCategory.name)
		sMsg += "the owner of it."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	if request.method == 'POST':

		# Delete all of the category items children before the parent category is deleted...
		lDeleteItems = session.query(Item).filter_by(category_id=oDeleteCategory.id).all()
		for oDeleteItem in lDeleteItems:
			deleteDBRec(oDeleteItem)

		sDeleteName = oDeleteCategory.name
		deleteDBRec(oDeleteCategory)

		sMsg = "Category '%s' deleted." % (sDeleteName)
		flash(sMsg)

		return redirect(url_for('showCategories'))
	else:
		return render_template('categoryDelete.html', Category2Delete=oDeleteCategory)

@app.route('/ShowLatestItemCreates')
def showLatestItemCreations():
	""" Display the 20 lastest item entries regardles of category."""
	ItemObjs = (session.query(Item, Category)
			 .join(Category).order_by(Item.createDt.desc())
			 .limit(20)
			 .values(Category.id,
			  Item.category_id,
			  Item.id,
			  Category.name,
			  Item.name,
			  Item.createDt ))

	lTmpObj = list(ItemObjs)	
	if len(lTmpObj)==0:
		sMsg  = "There are currently no cateory items in the system.  "
		flash(sMsg)
		return redirect(url_for('showCategories'))

	return render_template('categoryItemAllLatestCreated.html', ItemList=lTmpObj)

@app.route('/ShowCategoryItems/<int:category_id>/')
def showItemsInCategory(category_id):
	""" Show the items in a given category."""	
	lCatItems = session.query(Item).filter_by(category_id=category_id).order_by(Item.name).all()

	if len(lCatItems)==0:
		oCategory = session.query(Category).filter_by(id=category_id).first()

		if not oCategory:
			sMsg  = "Invalid category_id value, '%s', used in " % (category_id)
			sMsg += "'ShowCategoryItems' operation."
			flash(sMsg)
			return redirect(url_for('showCategories'))
		else:
			sMsg  = "There are currently no items for '%s'. " % (oCategory.name)
			sMsg += " Click the 'Create Item Entry' link to create."
			flash(sMsg)
			return render_template('categoryItemAll.html', ParentCategory=category_id, ItemList=lCatItems)
	else:
		return render_template('categoryItemAll.html', ParentCategory=category_id, ItemList=lCatItems)		

@app.route('/CatalogItemJSON/<int:category_id>')
@app.route('/CatalogAppItemJSON/<int:category_id>')
def showCategoryItemsJSON(category_id):
	""" Show all category item entries in JSON format."""
	lCategoryItems = session.query(Item).filter_by(category_id=category_id).all()
	return jsonify(CategoryItems=[categoryitem.serialize for categoryitem in lCategoryItems])

@app.route('/ShowSingleCategoryItemJSON/<int:item_id>/')
def showSingleCategoryItemJSON(item_id):
	""" Show an individual category item entry in JSON format."""
	oItem = session.query(Item).filter_by(id=item_id).first()

	if not oItem:
		sMsg  = "Invalid item_id value, '%s', used in " % (item_id)
		sMsg += "'ShowSingleCategoryItemJSON' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))
	else:
		return jsonify(CategoryItem=[oItem.serialize])

@app.route('/CreateCategoryItem/<int:category_id>/', methods=['GET', 'POST'])
def createItemInCategory(category_id):
	""" Create an item in a given category."""	
	if 'username' not in login_session:
		sMsg  = "You are not authorized to perform this '%s' " % ('create item category')
		sMsg += "action because you are not logged in.  You are being redirected to login."
		flash(sMsg)
		return redirect('/login')

	iSessionUser = getUserID(login_session['email'])
	if iSessionUser==None:
		sMsg  = "Fatal error!!!  Unable to find a matching Owner.id value for "
		sMsg += "unique session email address, '%s' " % (login_session['email'])
		sMsg += "during 'CreateCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=category_id))

	oCategory = session.query(Category).filter_by(id=category_id).first()

	if not oCategory:
		sMsg  = "Invalid category_id value, '%s', used in " % (category_id)
		sMsg += "'CreateCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=category_id))

	if oCategory.owner_id != iSessionUser:
		sMsg  = "You cannot create an item in '%s' because you are not " % (oCategory.name)
		sMsg += "the owner of it."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=category_id))

	if request.method == 'POST':
		if  request.form['ItemName'] == "":
			sMsg = "You must have an item name in order to complete the create."
			flash(sMsg)
			return render_template('categoryItemCreate.html', category_id=category_id)

		oNewItem    = Item(name=request.form['ItemName'], 
			               desc=request.form['ItemDesc'],
			               category_id=category_id,
			               owner_id=oCategory.owner_id)
		addDBRec(oNewItem)

		sMsg = "Item '%s' created in category." % (oNewItem.name)
		flash(sMsg)

		return redirect(url_for('showItemsInCategory', category_id=category_id))
	else:
		return render_template('categoryItemCreate.html', category_id=category_id)

@app.route('/ViewCategoryItem/<int:item_id>/')
def viewItemInCategory(item_id):
	""" View an item in a given category."""	
	oViewItem = session.query(Item).filter_by(id=item_id).first()

	if not oViewItem:
		sMsg  = "Invalid item_id value, '%s', used in " % (item_id)
		sMsg += "'ViewCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	return render_template('categoryItemView.html', ItemToView=oViewItem)

@app.route('/EditCategoryItem/<int:item_id>/', methods=['GET', 'POST'])
def editItemInCategory(item_id):
	""" Edit an item in a given category."""	
	if 'username' not in login_session:
		sMsg  = "You are not authorized to perform this '%s' " % ('edit item category')
		sMsg += "action because you are not logged in.  You are being redirected to login."
		flash(sMsg)
		return redirect('/login')

	oEditItem = session.query(Item).filter_by(id=item_id).first()

	if not oEditItem:
		sMsg  = "Invalid item_id value, '%s', used in " % (item_id)
		sMsg += "'EditCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	iSessionUser = getUserID(login_session['email'])
	if iSessionUser==None:
		sMsg  = "Fatal error!!!  Unable to find a matching Owner.id value for "
		sMsg += "unique session email address, '%s' " % (login_session['email'])
		sMsg += "during 'EditCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=oEditItem.category_id))

	if oEditItem.owner_id != iSessionUser:
		sMsg  = "You cannot edit item '%s' because you are not " % (oEditItem.name)
		sMsg += "the owner of it."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=oEditItem.category_id))

	if request.method == 'POST':
		if  request.form['ItemName'] == "":
			sMsg = "You must have an item name in order to complete the edit."
			flash(sMsg)
			return render_template('categoryItemEdit.html', ItemToEdit=oEditItem)

		sOrigName          = oEditItem.name
		oEditItem.name     = request.form['ItemName']
		oEditItem.desc     = request.form['ItemDesc']
		oEditItem.modifyDt = datetime.datetime.utcnow()

		updateDBRec(oEditItem)
		sMsg = ""
		if sOrigName == oEditItem.name:
			sMsg = "Item, '%s', content edited." % (oEditItem.name)
		else:
			sMsg = "Item '%s' name changed to '%s'." % (sOrigName, oEditItem.name)

		flash(sMsg)

		return redirect(url_for('showItemsInCategory', category_id=oEditItem.category_id))
	else:
		return render_template('categoryItemEdit.html', ItemToEdit=oEditItem)

@app.route('/DeleteCategoryItem/<int:item_id>/', methods=['GET', 'POST'])
def deleteItemInCategory(item_id):
	""" Delete an item in a given category."""	
	if 'username' not in login_session:
		sMsg  = "You are not authorized to perform this '%s' " % ('delete item category')
		sMsg += "action because you are not logged in.  You are being redirected to login."
		flash(sMsg)
		return redirect('/login')

	iSessionUser = getUserID(login_session['email'])
	if iSessionUser==None:
		sMsg  = "Fatal error!!!  Unable to find a matching Owner.id value for "
		sMsg += "unique session email address, '%s' " % (login_session['email'])
		sMsg += "during 'EditCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=category_id))

	oDeleteItem = session.query(Item).filter_by(id=item_id).first()

	if not oDeleteItem:
		sMsg  = "Invalid item_id value, '%s', used in " % (item_id)
		sMsg += "'DeleteCategoryItem' operation."
		flash(sMsg)
		return redirect(url_for('showCategories'))

	if oDeleteItem.owner_id != iSessionUser:
		sMsg  = "You cannot delete item '%s' because you are not " % (oDeleteItem.name)
		sMsg += "the owner of it."
		flash(sMsg)
		return redirect(url_for('showItemsInCategory', category_id=oDeleteItem.category_id))

	if request.method == 'POST':
		category_id = oDeleteItem.category_id
		sDeleteName = oDeleteItem.name
		deleteDBRec(oDeleteItem)

		sMsg = "Item '%s' deleteted from category." % (sDeleteName)
		flash(sMsg)

		return redirect(url_for('showItemsInCategory', category_id=category_id))
	else:
		return render_template('categoryItemDelete.html', Item2Delete=oDeleteItem)


if __name__ == '__main__':
	app.secret_key = 'category_catalog_project'
	app.debug = True
	app.run(host='0.0.0.0', port = 8000)
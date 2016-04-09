from flask import Flask, render_template, request, redirect, jsonify
from flask import url_for, flash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, Item, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import os

script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
rel_path = "client_secrets.json"
abs_file_path = os.path.join(script_dir, rel_path)
app = Flask(__name__)

CLIENT_ID = json.loads(
	open(abs_file_path, 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog"

# Connect to Database and create database session
engine = create_engine('postgresql://catalog:catalog@localhost:5432/catalog')
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)
session = DBSession()

# Show all catalogs
@app.route('/')
@app.route('/catalog')
def showCatalogs():
    catalogs = session.query(Catalog).order_by(Catalog.name)
    if 'user_id' not in login_session:
        return render_template('publicCatalogs.html', catalogs=catalogs)
    else:
        return render_template('catalogs.html', catalogs=catalogs)

# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/catalog/<int:catalog_id>/item/JSON')
def catalogitemJSON(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).first()
    items = session.query(Item).filter_by(
        catalog_id=catalog_id).all()
    if items:
        return jsonify(Items=[i.serialize for i in items])
    else:
        return jsonify(Items=[])

@app.route('/catalog/<int:catalog_id>/JSON')
def catalogJSON(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).first()
    if catalog is not None:
        return jsonify(Catalog=catalog.serialize)
    else:
        return jsonify(Catalog=[])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON')
def itemJSON(catalog_id, item_id):
    item = session.query(Item).filter_by(id=item_id).first()
    if item is not None:
        return jsonify(item=item.serialize)
    else:
        return jsonify(item=[])


@app.route('/catalog/JSON')
def allcatalogsJSON():
    catalogs = session.query(Catalog).all()
    if catalogs:
        return jsonify(catalogs=[c.serialize for c in catalogs])
    else:
        return jsonify(catalogs=[])

# Create a new catalog
@app.route('/catalog/new', methods=['GET', 'POST'])
def newCatalog():
    if 'user_id' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'],
            user_id=login_session['user_id'])
        session.add(newCatalog)
        session.commit()
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCatalog.html')

# Edit a catalog
@app.route('/catalog/<int:catalog_id>/edit', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    catalogToEdit = session.query(
        Catalog).filter_by(id=catalog_id).first()
    if 'user_id' not in login_session:
        return redirect('/login')
    if catalogToEdit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You aint authorized'+\
            ' to edit this Catalog. Please create your own catalog in order'+\
            ' to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            catalogToEdit.name = request.form['name']
            flash('Catalog Successfully Edited: %s' % catalogToEdit.name)
            return redirect(url_for('showCatalogs'))
    else:
        return render_template(
            'editCatalog.html', catalog=catalogToEdit)

# Delete a catalog
@app.route('/catalog/<int:catalog_id>/delete', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    if 'user_id' not in login_session:
        return redirect('/login')
    catalogToDelete = session.query(
        Catalog).filter_by(id=catalog_id).first()
    if catalogToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You aint authorized'+ \
          ' to delete this Catalog.Please create your own catalog in order'+ \
          ' to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(catalogToDelete)
        session.commit()
        flash('Catalog Successfully deleted: %s' % catalogToDelete.name)
        return redirect(
            url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template(
            'deleteCatalog.html', catalog=catalogToDelete)


# Show a catalog item
@app.route('/catalog/<int:catalog_id>')
@app.route('/catalog/<int:catalog_id>/item')
def showItem(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).first()
    owner = getUserInfo(catalog.user_id)
    items = session.query(Item).filter_by(
        catalog_id=catalog_id).all()
    if 'username' not in login_session or owner.id != login_session['user_id']:
        return render_template('publicItems.html', items=items,
                                catalog=catalog, owner=owner)
    else:
        return render_template('showItem.html', items=items, catalog=catalog,
                                owner=owner)

# Create a new item
@app.route(
    '/catalog/<int:catalog_id>/item/new', methods=['GET', 'POST'])
def newItem(catalog_id):
    if 'user_id' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form[
                           'description'], catalog_id=catalog_id,
                            user_id=login_session['user_id'])
        flash('Item Successfully created: %s' % newItem.name)
        session.add(newItem)
        session.commit()

        return redirect(url_for('showItem', catalog_id=catalog_id))
    else:
        return render_template('newItem.html', catalog_id=catalog_id)


# Edit a item
@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(catalog_id, item_id):
    if 'user_id' not in login_session:
        return redirect('/login')
    catalogToEdit = session.query(Catalog).filter_by(id=catalog_id).first()
    itemToEdit = session.query(Item).filter_by(id=item_id).first()
    if itemToEdit.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You aint authorized'+ \
            'to edit this item.Please create your own item in order '+\
            'to edit.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        if request.form['name']:
            itemToEdit.name = request.form['name']
        if request.form['description']:
            itemToEdit.description = request.form['description']
        session.add(itemToEdit)
        session.commit()
        flash('Item Successfully Edited %s' % itemToEdit.name)
        return redirect(url_for('showItem', catalog_id=catalog_id))
    else:
        return render_template(
            'editItem.html', catalog_id=catalog_id, item_id=item_id,
            item=itemToEdit)


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(catalog_id, item_id):
    if 'user_id' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).first()
    if itemToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You aint authorized'+\
            ' to delete this Item. Please create your own item in order'+\
            ' to delete.');}</script><body onload='myFunction()''>"
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully deleted: %s' % itemToDelete.name)
        return redirect(url_for('showItem', catalog_id=catalog_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets(abs_file_path, scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token

    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
        % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already'+
                    ' connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;\
        -webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    return output

# User Helper Functions
def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).first()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).first()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).first()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Execute HTTP GET request to revoke current token.
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % credentials
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    app.logger.info(result['status'])

    if result['status'] == '200':
        # Reset the user's session.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['picture']
        del login_session['email']
        del login_session['provider']
        del login_session['user_id']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

if __name__ == '__main__':
    app.debug = True
    app.secret_key = 'super_secret_key'
    app.run(host='0.0.0.0', port=5000)

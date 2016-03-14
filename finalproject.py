from flask import Flask, render_template, request, redirect, jsonify, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Catalog, Item

app = Flask(__name__)

engine = create_engine('postgresql:///catalog')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Fake Catalogs
# catalog = {'name': 'The CRUDdy Crab', 'id': '1'}

# catalogs = [{'name': 'The CRUDdy Crab', 'id': '1'}, {'name':'Blue Burgers', 'id':'2'},{'name':'Taco Hut', 'id':'3'}]


# Fake item Items
# items = [ {'name':'Cheese Pizza', 'description':'made with fresh cheese', 'price':'$5.99','course' :'Entree', 'id':'1'}, {'name':'Chocolate Cake','description':'made with Dutch Chocolate', 'price':'$3.99', 'course':'Dessert','id':'2'},{'name':'Caesar Salad', 'description':'with fresh organic vegetables','price':'$5.99', 'course':'Entree','id':'3'},{'name':'Iced Tea', 'description':'with lemon','price':'$.99', 'course':'Beverage','id':'4'},{'name':'Spinach Dip', 'description':'creamy dip with fresh spinach','price':'$1.99', 'course':'Appetizer','id':'5'} ]
# item =  {'name':'Cheese Pizza','description':'made with fresh cheese','price':'$5.99','course' :'Entree'}
# items = []


@app.route('/catalog/<int:catalog_id>/item/JSON')
def catalogitemJSON(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(Item).filter_by(
        catalog_id=catalog_id).all()
    return jsonify(Items=[i.serialize for i in items])


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/JSON')
def ItemJSON(catalog_id, item_id):
    item_Item = session.query(Item).filter_by(id=item_id).one()
    return jsonify(item_Item=item_Item.serialize)


@app.route('/catalog/JSON')
def catalogsJSON():
    catalogs = session.query(Catalog).all()
    return jsonify(catalogs=[r.serialize for r in catalogs])


# Show all catalogs
@app.route('/')
@app.route('/catalog/')
def showCatalogs():
    catalogs = session.query(Catalog).all()
    # return "This page will show all my catalogs"
    return render_template('catalogs.html', catalogs=catalogs)


# Create a new catalog
@app.route('/catalog/new/', methods=['GET', 'POST'])
def newCatalog():
    if request.method == 'POST':
        newCatalog = Catalog(name=request.form['name'])
        session.add(newCatalog)
        session.commit()
        return redirect(url_for('showCatalogs'))
    else:
        return render_template('newCatalog.html')
    # return "This page will be for making a new catalog"

# Edit a catalog


@app.route('/catalog/<int:catalog_id>/edit/', methods=['GET', 'POST'])
def editCatalog(catalog_id):
    editedCatalog = session.query(
        Catalog).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedCatalog.name = request.form['name']
            return redirect(url_for('showCatalogs'))
    else:
        return render_template(
            'editCatalog.html', catalog=editedCatalog)

    # return 'This page will be for editing catalog %s' % catalog_id

# Delete a catalog


@app.route('/catalog/<int:catalog_id>/delete/', methods=['GET', 'POST'])
def deleteCatalog(catalog_id):
    catalogToDelete = session.query(
        Catalog).filter_by(id=catalog_id).one()
    if request.method == 'POST':
        session.delete(catalogToDelete)
        session.commit()
        return redirect(
            url_for('showCatalogs', catalog_id=catalog_id))
    else:
        return render_template(
            'deleteCatalog.html', catalog=catalogToDelete)
    # return 'This page will be for deleting catalog %s' % catalog_id


# Show a catalog item
@app.route('/catalog/<int:catalog_id>/')
@app.route('/catalog/<int:catalog_id>/item/')
def showitem(catalog_id):
    catalog = session.query(Catalog).filter_by(id=catalog_id).one()
    items = session.query(Item).filter_by(
        catalog_id=catalog_id).all()
    return render_template('item.html', items=items, catalog=catalog)
    # return 'This page is the item for catalog %s' % catalog_id

# Create a new item item


@app.route(
    '/catalog/<int:catalog_id>/item/new/', methods=['GET', 'POST'])
def newItem(catalog_id):
    if request.method == 'POST':
        newItem = Item(name=request.form['name'], description=request.form[
                           'description'], catalog_id=catalog_id)
        session.add(newItem)
        session.commit()

        return redirect(url_for('showitem', catalog_id=catalog_id))
    else:
        return render_template('newItem.html', catalog_id=catalog_id)

    return render_template('newItem.html', catalog=catalog)
    # return 'This page is for making a new item item for catalog %s'
    # %catalog_id

# Edit a item item


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/edit',
           methods=['GET', 'POST'])
def editItem(catalog_id, item_id):
    editedItem = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['name']
        session.add(editedItem)
        session.commit()
        return redirect(url_for('showitem', catalog_id=catalog_id))
    else:

        return render_template(
            'editItem.html', catalog_id=catalog_id, item_id=item_id, item=editedItem)

    # return 'This page is for editing item item %s' % item_id

# Delete a item item


@app.route('/catalog/<int:catalog_id>/item/<int:item_id>/delete',
           methods=['GET', 'POST'])
def deleteItem(catalog_id, item_id):
    itemToDelete = session.query(Item).filter_by(id=item_id).one()
    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        return redirect(url_for('showitem', catalog_id=catalog_id))
    else:
        return render_template('deleteItem.html', item=itemToDelete)
    # return "This page is for deleting item item %s" % item_id


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

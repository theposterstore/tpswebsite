from flask import Flask, render_template,request
from pymongo import MongoClient
from bson import ObjectId  # Import ObjectId to use it for querying
from flask_paginate import Pagination, get_page_parameter



app = Flask(__name__)

# Connect to MongoDB
client = MongoClient("mongodb+srv://ThePosterStore:sKAGMckeTloe3TSv@theposterstore.f3beb.mongodb.net/")
db = client["TPS"]

@app.route('/home')
def home():
    # Fetch the last 4 items from the collection
    items_cursor = db['inventory'].find({}, {"_id": 0})  # Fetch all fields
    items_list = list(items_cursor.sort([('_id', -1)]).limit(4))  # Sort by _id in descending order and limit to 4
    
    # Pass the last 4 items to the template
    return render_template('index.html', items=items_list)

@app.route('/')
def index():
    # Fetch the last 4 items from the collection
    items_cursor = db['inventory'].find({}, {"_id": 0})  # Fetch all fields
    items_list = list(items_cursor.sort([('_id', -1)]).limit(4))  # Sort by _id in descending order and limit to 4
    
    # Pass the last 4 items to the template
    return render_template('index.html', items=items_list)

@app.route('/explore', methods=['GET'])
def explore():
    # Get search keyword and category from query parameters
    keyword = request.args.get('keyword', '')
    category = request.args.get('Category', '')

    # Build the query based on keyword and category
    query = {}
    if keyword:
        query['item_name'] = {'$regex': keyword, '$options': 'i'}  # Case-insensitive search
    if category and category != 'All Categories':
        query['collection_name'] = category

    # Use aggregation to fetch a random sample of 4 items
    pipeline = [
        {"$sample": {"size": 4}}  # Randomly select 4 documents
    ]
    random_cursor = db['inventory'].aggregate(pipeline)
    random_list = list(random_cursor)

    # Convert _id to string for each item in random_list
    for item in random_list:
        item['_id'] = str(item['_id'])

    # Pipeline to fetch unique collection names
    collection_names_cursor = db['inventory'].distinct('collection_name')
    collection_names_list = list(collection_names_cursor)

    # Get the current page and set the number of items per page
    page = request.args.get(get_page_parameter(), type=int, default=1)
    per_page = 8  # Number of items per page
    offset = (page - 1) * per_page

    # Fetch all items based on the search and category filter, with pagination and sorting
    all_items_cursor = db['inventory'].find(query, {"_id": 1, "item_name": 1, "image_url": 1, "collection_name": 1}).sort("_id", -1).skip(offset).limit(per_page)
    all_items_list = list(all_items_cursor)
    
    # Convert _id to string for each item in all_items_list
    for item in all_items_list:
        item['_id'] = str(item['_id'])

    # Total number of items for pagination
    total = db['inventory'].count_documents(query)

    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page

    # Manual pagination handling
    has_prev = page > 1
    has_next = page < total_pages

    return render_template('explore.html', 
                           random_list=random_list, 
                           collection_names=collection_names_list, 
                           all_items_list=all_items_list, 
                           page=page, 
                           total_pages=total_pages, 
                           has_prev=has_prev, 
                           has_next=has_next, 
                           keyword=keyword, 
                           category=category,
                           max=max,
                           min=min)

@app.route('/item/<item_id>', methods=['GET'])
def item_details(item_id):
    # Convert string item_id to ObjectId
    item = db['inventory'].find_one({"_id": ObjectId(item_id)})

    if item:
        return render_template('item_details.html', item=item)
    else:
        return "Item not found", 404
    

if __name__ == '__main__':
    app.run(debug=True)

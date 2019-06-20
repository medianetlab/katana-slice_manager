from pymongo import MongoClient
from pprint import pprint
import yaml
import json

client = MongoClient("mongodb://mongo")
db = client.katana

collection = db.vim


def index(collection_name):
    collection = db[collection_name]
    return collection.find({})


def get(collection_name, uuid):
    collection = db[collection_name]
    return collection.find_one({"_id": uuid})


def add(collection_name, json_data):
    collection = db[collection_name]
    return collection.insert_one(json_data).inserted_id


def add_many(collection_name, list_data):
    collection = db[collection_name]
    return collection.insert_many(list_data).inserted_ids


def delete(collection_name, uuid):
    result = db[collection_name].delete_one({"_id": uuid}).deleted_count
    return result


def update(collection_name, uuid, json_data):
    return db[collection_name].replace_one({"_id": uuid}, json_data).modified_count


def count(collection_name):
    collection = db[collection_name]
    return collection.count_documents({})


def find(collection_name, data={}):
    collection = db[collection_name]
    return collection.find_one(data)

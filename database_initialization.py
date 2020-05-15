#!/usr/bin/env python



'''
Database initialization should be used when
new collection is added.

For all empty collection the corresponding
root document and indexes are created.

For all collections the existing indexes
are printed.

With force argument all data from database
are deleted, use with caution!
'''



import argparse
from pymongo import MongoClient, TEXT
from flask import g
import ipapi


app = ipapi.create_app()


client = MongoClient('mongodb://127.0.0.1:27017')
db = client.ipapi
parser = argparse.ArgumentParser(description='Databse ipapi initialization')
parser.add_argument('--force_delete_all_data',
                    action = 'store_true',
                    help = 'Forcefully delete all data from ipapi database',
                    required = False)
args = parser.parse_args()


with app.app.app_context():
  ipapi.log.w('please check if LOGLEVEL is DEBUG')
  #create text indexes and root documents for all collections
  g._user_name = g._provider_name = 'root'
  g._user_ip = g._provider_ip = '127.0.0.1'
  collections = [i for i in ipapi.base.collections()]
  ipapi.log.d(f'Collections: {collections}')
  for i in collections:
    if args.force_delete_all_data:
      ipapi.log.w(f'Deleting collection {i}')
      db.drop_collection(i)
    else:
      ipapi.log.i(f'Not deleting collection {i}')
    if db[i].count() == 0:
      ipapi.log.i(f'Creating text index for collection {i}')
      db[i].create_index([('name', TEXT), ('description', TEXT)],
                        weights = {'name': 10, 'description': 1})
      data = {}
      data['description'] = f'Root {i} document'
      if i == 'ipv4':
        db[i].create_index([('scope', 1), 
                            ('_meta._first', 1), 
                            ('_meta._last', 1)])
        data['name'] = '0.0.0.0'
        data['prefix'] = 0
        data['scope'] = 'global'
        ii = ipapi.ipv4(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['ipv4'] = [ii.data['_id']]
        root_ipv4 = db.ipv4.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
      elif i == 'user':
        data['name'] = 'root'
        ii = ipapi.user(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['user'] = [ii.data['_id']]
        root_user = db.user.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
      elif i == 'group':
        data['name'] = 'root'
        ii = ipapi.group(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['group'] = [ii.data['_id']]
        root_group = db.group.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
        
        data['name'] = 'root_delete'
        ii = ipapi.group(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['group'] = [root_group]
        root_delete_group = db.group.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
        
        data['name'] = 'root_get'
        ii = ipapi.group(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['group'] = [root_group]
        root_get_group = db.group.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
        
        data['name'] = 'root_patch'
        ii = ipapi.group(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['group'] = [root_group]
        root_patch_group = db.group.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
        
        data['name'] = 'root_post'
        ii = ipapi.group(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['group'] = [root_group]
        root_post_group = db.group.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
        
        data['name'] = 'root_put'
        ii = ipapi.group(data, 'database_initialization')
        ii.data['_meta']['_version'] = 1
        ii.data['_meta']['_uuid_valid'] = ii.data['_id']
        ii.data['parents'] = {}
        ii.data['parents']['group'] = [root_group]
        root_put_group = db.group.insert_one(ii.data).inserted_id
        ipapi.log.i(f'Created document {ii.data}')
      else:
        ipapi.log.e(f'Unhandled {i}')
    else:
      ipapi.log.w(f'Skipping initialization, {i} is not empty!')
    ipapi.log.i(f'Listing indexes for {i}')
    for j in db[i].list_indexes():
      ipapi.log.i(f'\t{j}')
  if args.force_delete_all_data:
    #assing user root to parent groups
    r = db.user.update_one({'_id': root_user}, {'$set': {'parents': {'group': [
      root_delete_group,
      root_get_group,
      root_patch_group,
      root_post_group,
      root_put_group]}}}).modified_count
    ipapi.log.i(f'{r} user added to root group')
    #create access for root documents
    root_access =  {
      'delete': [root_delete_group],
      'get': [root_get_group],
      'patch': [{'match': '.', 'patch': [root_patch_group]}],
      'post': [root_post_group],
      'put': [root_put_group]}
    for i in collections:
      #update all
      if i == 'ipv4':
        r = db.ipv4.update_many({}, {'$set': {'access': root_access}})
        ipapi.log.i(f'Access added to {r.modified_count} root {i} documents')
      elif i == 'user':
        r = db.user.update_many({}, {'$set': {'access': root_access}})
        ipapi.log.i(f'Access added to {r.modified_count} root {i} documents')
      elif i == 'group':
        r = db.group.update_many({}, {'$set': {'access': root_access}})
        ipapi.log.i(f'Access added to {r.modified_count} root {i} documents')
      else:
        ipapi.log.e(f'Unhandled {i}')

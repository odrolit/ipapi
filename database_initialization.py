#!/usr/bin/env python



'''
Database initialization should be used when
new collection is added.

For all empty collection the corresponding
root document and indexes are created.

For all collections the existing indexes
are printed.

With force argument this all data from database
are deleted, use with caution!
'''



import argparse
from pymongo import MongoClient, TEXT
import ipapi



client = MongoClient('mongodb://127.0.0.1:27017')
db = client.ipapi
parser = argparse.ArgumentParser(description='Databse ipapi initialization')
parser.add_argument('--force_delete_all_data',
                    action = 'store_true',
                    help = 'Forcefully delete all data from ipapi database',
                    required = False)
args = parser.parse_args()



#create text indexes for all collections
for i in ipapi.base.collections():
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
    data['_user_name'] = 'root'
    data['_user_ip'] = '127.0.0.1'
    if i == 'ipv4':
      data['name'] = '0.0.0.0/0'
      ii = ipapi.ipv4(data, 'database_initialization')
      #_set_parents loop hook
      ii.data['parents'] = {}
      ii.data['parents']['ipv4'] = [ii.data['_id']]
      db.ipv4.insert_one(ii.data)
      ipapi.log.i(f'Created document {ii.data}')
    else:
      ipapi.log.e(f'Unhandled {i}')
  else:
    ipapi.log.w(f'Skipping initialization, {i} is not empty!')
  ipapi.log.i(f'Listing indexes for {i}')
  for j in db[i].list_indexes():
    ipapi.log.i(f'\t{j}')

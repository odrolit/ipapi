#!/usr/bin/env python

from ipapi import app

if __name__ == '__main__':
  app.run(
    host='0.0.0.0',
    port=5000,
  )

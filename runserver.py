#!/usr/bin/env python

import ipapi



if __name__ == '__main__':
  ipapi.app.run(
    host='0.0.0.0',
    port=5000,
    debug = True,
  )

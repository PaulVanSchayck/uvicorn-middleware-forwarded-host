#!/bin/bash
exec gunicorn example:app\
  --workers 1\
  --worker-class example.MyUvicornWorker \
  --bind 0.0.0.0:8000

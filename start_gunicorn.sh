#!/bin/bash

if [ "$ENV" = "production" ]; then
  gunicorn app:app --workers 3 --bind unix:/run/gunicorn.sock
else
  gunicorn app:app --workers 3 --bind 127.0.0.1:8000
fi
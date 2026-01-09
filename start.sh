#!/usr/bin/env bash

echo "Running database migrations..."
flask db upgrade

echo "Starting gunicorn..."
gunicorn app:app

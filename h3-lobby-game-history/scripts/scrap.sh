#!/usr/bin/env bash


source .env
export DATABASE_URL

pushd src
  while :; do
    PYTHONPATH=. poetry run python proxy/proxy.py --standalone
    sleep 600s
  done
popd

#!/usr/bin/env bash
for i in {1..10}; do
  nc -z 127.0.0.1 2222 >/dev/null 2>&1
  sleep 0.1
done

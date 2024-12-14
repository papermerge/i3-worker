#!/bin/sh

exec_worker() {
  echo "now in exec_worker"
  exec poetry run celery  -A i3worker.celery_app worker ${I3_WORKER_ARGS}
}

case $1 in
  worker)
    exec_worker
    ;;
  *)
    exec "$@"
    ;;
esac

#!/usr/bin/env bash
#
# Deploy the BarberApp API on the server.
#
# Runs ON the host, from the application directory:
#
#   ssh -i <key>.pem ubuntu@<host>
#   cd ~/barberapp
#   ./scripts/deploy.sh
#
# In order: verify the working directory, back up the database BEFORE
# touching anything, fetch the new commit, rebuild the image, start the
# container (its command runs `alembic upgrade head` first), and wait for
# /health. Any failure stops the script and leaves the previous container
# serving.
set -euo pipefail

BRANCH="${BRANCH:-main}"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.prod.yml}"
ENV_FILE="${ENV_FILE:-.env.prod}"
DB_CONTAINER="${DB_CONTAINER:-data-center-db-1}"
DB_NAME="${DB_NAME:-barberapp}"
DB_SUPERUSER="${DB_SUPERUSER:-app}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/backups}"

dc() { docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"; }

say() { printf '\n==> %s\n' "$1"; }

say "Checking the working directory"
[ -f "$COMPOSE_FILE" ] || {
  echo "Missing $COMPOSE_FILE. Run this from ~/barberapp."
  exit 1
}
[ -f "$ENV_FILE" ] || {
  echo "Missing $ENV_FILE. Copy .env.prod.example and fill it in."
  exit 1
}

say "Backing up the database first"
mkdir -p "$BACKUP_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
DUMP="$BACKUP_DIR/$DB_NAME-$STAMP.sql.gz"
docker exec "$DB_CONTAINER" pg_dump -U "$DB_SUPERUSER" -d "$DB_NAME" | gzip > "$DUMP"
echo "Backup: $DUMP"

say "Fetching $BRANCH"
git fetch --prune origin
git checkout "$BRANCH"
git reset --hard "origin/$BRANCH"
git --no-pager log -1 --oneline

say "Building the image"
dc build api

say "Starting the container (migrations run before uvicorn)"
dc up -d api

say "Waiting for /health"
for attempt in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:8001/health >/dev/null 2>&1; then
    echo "Healthy after ${attempt} attempts."
    curl -fsS http://127.0.0.1:8001/health
    echo
    say "Deployment complete"
    exit 0
  fi
  sleep 2
done

say "FAILED: /health never answered"
dc logs --tail 60 api
cat <<ROLLBACK

Roll back with:

  cd ~/barberapp
  git reset --hard <previous-commit>
  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE up -d --build api

Restore the database with:

  gunzip -c $DUMP | docker exec -i $DB_CONTAINER psql -U $DB_SUPERUSER -d $DB_NAME

ROLLBACK
exit 1

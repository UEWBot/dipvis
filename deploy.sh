#!/usr/bin/env bash
#
# Update a running DipTV site to the latest code.
#
# Usage, on the server, from anywhere:
#     ./deploy.sh
#
# This is how the main DipTV site is deployed: a git checkout, a Python
# virtual environment, gunicorn managed by systemd, and a server-only branch
# holding deployment-specific commits (database settings, etc.) whose
# upstream is origin/master.
#
# If your server is set up differently, the parts you are most likely to need
# to change are marked "CONFIGURE". Each can also be overridden with an
# environment variable, e.g.:
#     VENV_DIR=/srv/dipvis/venv GUNICORN_SERVICE=dipvis ./deploy.sh

# Stop at the first failure, so we never restart the site half-updated.
set -euo pipefail

# The repository root is wherever this script lives.
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The Django project (the directory containing manage.py).
DJANGO_DIR="$REPO_DIR/visualiser"

# CONFIGURE: the Python virtual environment the site runs in.
# Using its python directly (rather than "activating" it) works the same from
# an interactive shell, ssh, cron, or a git hook.
VENV_DIR="${VENV_DIR:-$REPO_DIR/.venv}"
PYTHON="$VENV_DIR/bin/python"

# CONFIGURE: the systemd service that runs gunicorn for the site.
GUNICORN_SERVICE="${GUNICORN_SERVICE:-gunicorn}"

# CONFIGURE: how to pull the latest code.
# A plain "git pull" uses whatever your git config says. On a server branch
# that carries its own deployment commits on top of origin/master, you may
# prefer "git pull --rebase" (keeps those commits on top) or
# "git pull --ff-only" (if the server has no local commits).
GIT_PULL="${GIT_PULL:-git pull}"

if [ ! -x "$PYTHON" ]; then
    echo "No Python found at $PYTHON - set VENV_DIR to the site's virtual environment" >&2
    exit 1
fi

# compilemessages (below) needs the GNU gettext tools,
# e.g. "sudo apt-get install gettext" on Debian/Ubuntu.
if ! command -v msgfmt > /dev/null; then
    echo "msgfmt not found - install GNU gettext to compile translations" >&2
    exit 1
fi

cd "$REPO_DIR"

# Refuse to deploy over uncommitted changes, which "git pull" could clash with
# and which wouldn't be in any branch.
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "There are uncommitted changes in $REPO_DIR - commit or stash them first" >&2
    exit 1
fi

echo "== Updating the code"
$GIT_PULL

echo "== Installing Python dependencies"
"$PYTHON" -m pip install -r requirements.txt

cd "$DJANGO_DIR"

echo "== Applying database migrations"
"$PYTHON" manage.py migrate --noinput

# The compiled .mo files aren't kept in git, so they are rebuilt each time.
echo "== Compiling translations"
"$PYTHON" manage.py compilemessages

# Only needed if the web server serves static files (CSS, images) from
# STATIC_ROOT, which has to be set in the server's settings.
# (--no-imports stops the shell printing a message that would end up in the result.)
STATIC_ROOT="$("$PYTHON" manage.py shell --no-imports -c 'from django.conf import settings; print(settings.STATIC_ROOT or "")')"
if [ -n "$STATIC_ROOT" ]; then
    echo "== Collecting static files into $STATIC_ROOT"
    "$PYTHON" manage.py collectstatic --noinput
else
    echo "== STATIC_ROOT isn't set, so not collecting static files"
fi

# Warns about insecure production settings (e.g. DEBUG left on), and fails on
# outright errors before the site is restarted.
echo "== Checking the deployment settings"
"$PYTHON" manage.py check --deploy

# CONFIGURE: how the site is restarted. This needs permission to restart the
# service, e.g. a sudoers rule allowing "systemctl restart <service>".
echo "== Restarting $GUNICORN_SERVICE"
sudo systemctl restart "$GUNICORN_SERVICE"
systemctl is-active --quiet "$GUNICORN_SERVICE" || {
    echo "$GUNICORN_SERVICE failed to start - see: journalctl -u $GUNICORN_SERVICE" >&2
    exit 1
}

echo "== Deployed $(git -C "$REPO_DIR" log -1 --format='%h %s')"

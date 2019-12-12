#!/bin/bash

# As seen in http://tutos.readthedocs.org/en/latest/source/ndg.html

SAAP_DIR="/var/interlegis/saap"

# Seta um novo diretório foi passado como raiz para o SAAP
# caso esse tenha sido passado como parâmetro
if [ "$1" ]
then
    SAAP_DIR="$1"
fi

NAME="SAAP"                                     # Name of the application (*)
DJANGODIR=/var/interlegis/saap/                    # Django project directory (*)
SOCKFILE=/var/interlegis/saap/run/gunicorn.sock    # we will communicate using this unix socket (*)
USER=`whoami`                                   # the user to run as (*)
GROUP=`whoami`                                  # the group to run as (*)
NUM_WORKERS=3                                   # how many worker processes should Gunicorn spawn (*)
                                                # NUM_WORKERS = 2 * CPUS + 1
TIMEOUT=960
#GRACEFUL_TIMEOUT=480
MAX_REQUESTS=100                                # number of requests before restarting worker
DJANGO_SETTINGS_MODULE=saap.settings            # which settings file should Django use (*)
DJANGO_WSGI_MODULE=saap.wsgi                    # WSGI module name (*)

echo "Starting $NAME as `whoami` on base dir $SAAP_DIR"

# parameter can be passed to run without virtualenv
if [[ "$@" != "no-venv" ]]; then
    # Activate the virtual environment
    cd $DJANGODIR
    source /var/interlegis/.virtualenvs/saap/bin/activate
    export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
    export PYTHONPATH=$DJANGODIR:$PYTHONPATH
fi

# Create the run directory if it doesn't exist
RUNDIR=$(dirname $SOCKFILE)
test -d $RUNDIR || mkdir -p $RUNDIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $NAME \
  --log-level debug \
  --workers $NUM_WORKERS \
  --max-requests $MAX_REQUESTS \
  --user $USER \
  --access-logfile /var/log/saap/access.log \
  --error-logfile /var/log/saap/error.log \
  --bind=unix:$SOCKFILE
  --timeout $TIMEOUT
  #--graceful-timeout $GRACEFUL_TIMEOUT


web:       newrelic-admin run-program python manage.py run_gunicorn -b 0.0.0.0:$PORT -w 9 -k gevent --max-requests 250
scheduler: newrelic-admin run-program python manage.py celeryd -E -B --loglevel=INFO
worker:    newrelic-admin run-program python manage.py celeryd -E --loglevel=INFO

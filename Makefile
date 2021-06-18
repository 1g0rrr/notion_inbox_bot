# Set the default goal if no targets were specified on the command line
.DEFAULT_GOAL = run
# Makes shell non-interactive and exit on any error
.SHELLFLAGS = -ec

docker-run-dev:  ## Runs dev server in docker
	python ./utils/wait_for_postgres.py
	python manage.py migrate
	python manage.py runserver 0.0.0.0:8000

# docker-run-production:  ## Runs production server in docker
# 	python ./utils/wait_for_postgres.py
# 	python manage.py migrate
# 	python manage.py runserver 0.0.0.0:8000

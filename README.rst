============================
Simple async jobs django app
============================

    Simple async jobs is a Django app that provides you a simple way
    for running periodic and one off jobs using django management commands.

Installation
------------

``pip install django-simple-async-jobs``

Quick start
-----------

1. Add "simple_jobs" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'simple_jobs',
    ]

2. Setup the following settings::

    JOB_POLLER_TIMEOUT_BEFORE_KILLED = 60

    DEFAULT_LOGGER_NAME = "jobs"
    PERIODIC_JOBS_LOGGER_NAME = "periodic_jobs"
    ONE_OFF_JOBS_LOGGER_NAME = "one_off_jobs"

    DEFAULT_MAX_ONE_OFF_JOBS_RUNS_PER_LIFE = 10
    DEFAULT_MAX_PERIODIC_JOBS_RUNS_PER_LIFE = 50

    DEFAULT_MAX_JOB_RETRIES = 6
    DEFAULT_JOB_RETRY_SECONDS_INTERVAL = 900

3. Run ``python manage.py migrate`` to create the jobs models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a Job (you'll need the Admin app enabled).

5. Run the ``python manage.py one_off_job_poller`` or ``python manage.py periodic_job_poller``.


It's recommended to use one of the django management commands as CMD for docker container in docker-compose config with parameter restart=always.
Example::

  worker-one-off-jobs: 
    build: .
    container_name: "worker-one-off"
    restart: "always"
    command: python manage.py one_off_job_poller


The lifetime of container consists of the following::

    1) retrieve jobs
    2) execute jobs until the limit is hit
    3) sleep for time specified in settings
    4) exit

Once container is dead it will be launched again by docker-compose.

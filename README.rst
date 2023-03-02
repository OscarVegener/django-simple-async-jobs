=====
Simple async jobs
=====

Simple async jobs is a Django app that provides you a simple way
for running periodic and one off jobs using django management commands.

Quick start
-----------

1. Add "simple_jobs" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'simple_jobs',
    ]

2. Setup the settings like this::

    JOB_POLLER_TIMEOUT_BEFORE_KILLED = 60

    DEFAULT_LOGGER_NAME = "jobs"
    PERIODIC_JOBS_LOGGER_NAME = "periodic_jobs"
    ONE_OFF_JOBS_LOGGER_NAME = "one_off_jobs"

    DEFAULT_MAX_ONE_OFF_JOBS_RUNS_PER_LIFE = 10
    DEFAULT_MAX_PERIODIC_JOBS_RUNS_PER_LIFE = 50

    DEFAULT_MAX_JOB_RETRIES = 6
    DEFAULT_JOB_RETRY_SECONDS_INTERVAL = 900

3. Run ``python manage.py migrate`` to create the polls models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a Job (you'll need the Admin app enabled).

5. Run the ``python manage.py one_off_job_poller`` or ``python manage.py periodic_job_poller``.
It's recommended to use one of these command as CMD for docker container in docker-compose config with parameter restart=always.
The lifetime of container consists of the following:
- retrieve jobs
- execute jobs until the limit is hit
- sleep for time specified in settings
- exit
Once container is dead it will be started again by docker-compose.

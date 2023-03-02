from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

SETTINGS = [
    ("JOB_POLLER_TIMEOUT_BEFORE_KILLED", int),
    ("DEFAULT_LOGGER_NAME", str),
    ("PERIODIC_JOBS_LOGGER_NAME", str),
    ("ONE_OFF_JOBS_LOGGER_NAME", str),
    ("DEFAULT_MAX_ONE_OFF_JOBS_RUNS_PER_LIFE", int),
    ("DEFAULT_MAX_PERIODIC_JOBS_RUNS_PER_LIFE", int),
    ("DEFAULT_MAX_JOB_RETRIES", int),
    ("DEFAULT_JOB_RETRY_SECONDS_INTERVAL", int),
]


def check_for_setting(setting_name, variable_type):
    if not hasattr(settings, setting_name):
        raise ImproperlyConfigured(f"{setting_name} is not set in django settings.")

    setting_val = getattr(settings, setting_name)

    if type(setting_val) != variable_type:
        raise ImproperlyConfigured(
            f"{setting_name} is of wrong variable type. Is {type(setting_val)} instead of {variable_type}"
        )


def check_settings():
    for setting_name, variable_type in SETTINGS:
        check_for_setting(setting_name, variable_type)


check_settings()

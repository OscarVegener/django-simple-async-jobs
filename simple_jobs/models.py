import importlib
import logging
import traceback
import uuid

from django import db
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class JobStatusChoices(models.TextChoices):
    # job is ready to be executed
    pending = "PENDING", _("Pending")
    # worker has started executing the job
    in_progress = "IN_PROGRESS", _("In progress")
    # job's function resulted in an Exception
    failed = "FAILED", _("Failed")
    # job's function executed successfully
    success = "SUCCESS", _("Success")


class Job(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    function_name = models.TextField()
    function_arguments = models.JSONField(default=dict, blank=True)

    status = models.TextField(
        choices=JobStatusChoices.choices, default=JobStatusChoices.pending
    )

    is_one_off = models.BooleanField()  # indicates whether the job will run only once
    periodic_schedule = models.TextField(null=True, blank=True)

    disabled = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_run_at = models.DateTimeField(null=True, blank=True)

    allow_retries = models.BooleanField(
        default=True
    )  # indicates whether the job will use retries
    is_scheduled_for_retry = models.BooleanField(default=False)
    retry_times = models.IntegerField(default=0)
    max_retries = models.IntegerField(default=settings.DEFAULT_MAX_JOB_RETRIES)
    retry_seconds_interval = models.IntegerField(
        default=settings.DEFAULT_JOB_RETRY_SECONDS_INTERVAL
    )

    queue = models.TextField(
        null=True, blank=True
    )  # can be used for organizing multiple queues

    def _reset_retry(self):
        """
        Resets retry_times and is_scheduled_for_retry to it's default values if needed.
        Does not save the object.
        """
        if self.allow_retries and self.is_scheduled_for_retry:
            self.retry_times = 0
            self.is_scheduled_for_retry = False

    def _schedule_for_retry(self):
        """
        Schedules the job for retry if allowed.
        Does not save the object.
        """
        if self.allow_retries:
            self.is_scheduled_for_retry = True

    def run(self, logger=None):
        self.status = JobStatusChoices.in_progress
        self.save()

        if logger is not None:
            JOB_LOGGER = logger
        else:
            JOB_LOGGER = logging.getLogger(settings.DEFAULT_LOGGER_NAME)

        JOB_LOGGER.debug(f"Started running Job #{self.id}")

        started_at = timezone.now()

        try:
            module_name, function_name = self.function_name.rsplit(".", 1)
            module = importlib.import_module(module_name)
            function = getattr(module, function_name)

            result = function(**self.function_arguments)

            JOB_LOGGER.info(f"Result of Job #{self.id}: {result}")

            finished_at = timezone.now()

            JobResult.objects.create(
                job=self,
                result=result,
                started_at=started_at,
                finished_at=finished_at,
            )

            self._reset_retry()

            self.status = JobStatusChoices.success
            self.last_run_at = finished_at

        except Exception as e:
            exc_type = type(e).__name__
            exc_message = str(e)
            exc_traceback = traceback.format_exc()

            finished_at = timezone.now()

            JobResult.objects.create(
                job=self,
                exc_type=exc_type,
                exc_message=exc_message,
                exc_traceback=exc_traceback,
                started_at=started_at,
                finished_at=finished_at,
            )

            JOB_LOGGER.error(
                f"Exception in Job #{self.id}",
                extra={
                    "exc_type": exc_type,
                    "exc_message": exc_message,
                    "exc_traceback": exc_traceback,
                },
            )

            self.status = JobStatusChoices.failed
            self.last_run_at = finished_at

            # schedule the task for retry
            self._schedule_for_retry()

        finally:
            if (
                self.allow_retries
                and not self.is_scheduled_for_retry
                and self.is_one_off
            ):
                self.disabled = True

            self.save()

            db.close_old_connections()

        JOB_LOGGER.debug(f"Finished running Job #{self.id}")


class JobResult(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="results")
    result = models.JSONField(null=True, blank=True)

    exc_type = models.TextField(null=True, blank=True)
    exc_message = models.TextField(null=True, blank=True)
    exc_traceback = models.TextField(null=True, blank=True)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField()

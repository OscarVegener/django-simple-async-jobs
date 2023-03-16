import datetime
from logging import getLogger
from typing import List, Union

import croniter
from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone

from simple_jobs.constants import GENERAL_PERIODIC_JOBS
from simple_jobs.management.commands.base_job_poller import BaseJobPoller
from simple_jobs.models import Job, JobStatusChoices

LOGGER = getLogger(settings.PERIODIC_JOBS_LOGGER_NAME)


class Command(BaseJobPoller):
    help = "Polls periodic jobs"

    def __init__(self, *args, **kwargs):
        super().__init__(
            LOGGER,
            GENERAL_PERIODIC_JOBS,
            settings.DEFAULT_MAX_PERIODIC_JOBS_RUNS_PER_LIFE,
            *args,
            **kwargs,
        )

    async def _is_job_ready_by_cron(self, job: Job) -> bool:
        if job.status == JobStatusChoices.pending:
            return True

        try:
            base = job.last_run_at
            cron_schedule = job.periodic_schedule
            iteration = croniter.croniter(cron_schedule, base)

            next_datetime = iteration.get_next(datetime.datetime)
            now_datetime = timezone.now()

            return next_datetime < now_datetime

        except Exception:
            self.LOGGER.warning(
                f"Job #{job.id} have incorrect schedule. Job is marked as not ready."
            )
            return False

    async def _is_job_ready(self, job: Job) -> bool:
        is_pre_ready = await super()._is_job_ready(job)

        if job.allow_retries and job.is_scheduled_for_retry:
            now = timezone.now()
            if now >= job.last_run_at + datetime.timedelta(
                seconds=job.retry_seconds_interval
            ):
                self.LOGGER.info(
                    f"Job #{job.id} is ready because it is scheduled for retry."
                )
                return is_pre_ready and True
        else:
            return is_pre_ready and await self._is_job_ready_by_cron(job)

    def _get_jobs_query(self) -> Union[QuerySet, List[Job]]:
        return super()._get_jobs_query().filter(is_one_off=False)

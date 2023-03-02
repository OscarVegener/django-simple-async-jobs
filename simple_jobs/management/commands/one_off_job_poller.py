from logging import getLogger
from typing import List, Union

from django.conf import settings
from django.db.models import QuerySet
from simple_jobs.constants import GENERAL_ONE_OFF_JOBS
from simple_jobs.management.commands.base_job_poller import BaseJobPoller
from simple_jobs.models import Job, JobStatusChoices

LOGGER = getLogger(settings.ONE_OFF_JOBS_LOGGER_NAME)


class Command(BaseJobPoller):
    help = "Polls one time jobs"

    def __init__(self, *args, **kwargs):
        super().__init__(
            LOGGER,
            GENERAL_ONE_OFF_JOBS,
            settings.DEFAULT_MAX_ONE_OFF_JOBS_RUNS_PER_LIFE,
            *args,
            **kwargs
        )

    def _get_jobs_query(self) -> Union[QuerySet, List[Job]]:
        return super()._get_jobs_query().filter(is_one_off=True)

    async def _is_job_ready(self, job: Job) -> bool:
        is_pre_ready = await super()._is_job_ready(job)
        return is_pre_ready and job.status == JobStatusChoices.pending

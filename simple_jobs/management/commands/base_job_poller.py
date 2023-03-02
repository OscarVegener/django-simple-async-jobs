import asyncio
import logging
import time
from typing import List, Union

from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import DatabaseError
from django.db.models import QuerySet
from simple_jobs.models import Job, JobStatusChoices


class BaseJobPoller(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--queue", type=str, default=None)
        parser.add_argument("--logger-name", type=str, default=None)

    def __init__(
        self,
        logger: logging.Logger,
        job_type_name: str,
        max_jobs_run_qty: str,
        *args,
        **kwargs,
    ):
        """
        Args:
            logger: logger for the poller
            job_type_name: name used to identify the type of jobs for this poller
            max_jobs_run_qty: max quantity of job runs until poller finishes it's execution
        """
        super().__init__(*args, **kwargs)
        self.LOGGER = logger
        self.job_type_name = job_type_name
        self.max_jobs_run_qty = max_jobs_run_qty
        self.job_run_qty = 0  # how many jobs poller already executed

    def _get_jobs_query(self) -> Union[QuerySet, List[Job]]:
        base_query = Job.objects.filter(disabled=False)

        if self.queue is not None:
            return base_query.filter(queue=self.queue)

        return base_query

    @sync_to_async
    def _get_jobs(self) -> List[Job]:
        try:
            jobs = list(self._get_jobs_query())
            return jobs
        except DatabaseError:
            self.LOGGER.warning("DB migrations are not done yet!")
            time.sleep(100)
            return []

    @sync_to_async
    def _increase_retries_for_job(self, job: Job):
        job.retry_times += 1
        job.save()

    async def _execute_job(self, job: Job):
        if job.allow_retries and job.is_scheduled_for_retry:
            await self._increase_retries_for_job(job)

        await sync_to_async(job.run)(logger=self.LOGGER)
        self.job_run_qty += 1

    async def _is_job_ready(self, job: Job) -> bool:
        """Check whether job is ready for execution

        Returns:
            bool: True if job is ready for execution otherwise False
        """
        if job.allow_retries and job.is_scheduled_for_retry:
            if job.retry_times < job.max_retries:
                return True
            return False

        return True

    async def _start_job_execution(self, job: Job):
        try:
            if self.job_run_qty >= self.max_jobs_run_qty:
                self.LOGGER.info(
                    f"Max jobs run qty reached: {self.max_jobs_run_qty}."
                    f"Worker is going to restart after all existing asyncio tasks yield this log."
                )
                return
            if await self._is_job_ready(job):
                await self._execute_job(job)
        except Exception as e:
            self.LOGGER.error(f"Exception in job #{job.id}: {e}")

    async def _asyncio_main_func(self):
        jobs = await self._get_jobs()
        self.LOGGER.debug("Got {} jobs: {}".format(self.job_type_name, jobs))

        await asyncio.gather(*[self._start_job_execution(job) for job in jobs])

    def _mark_hanging_jobs_as_pending(self) -> Union[QuerySet, List[Job]]:
        """Checks if there are hanging jobs with "In Progress" status and sets them to "Pending"

        Returns:
            Union[QuerySet, List[Job]]: queryset of jobs
        """
        return (
            self._get_jobs_query()
            .filter(status=JobStatusChoices.in_progress)
            .update(status=JobStatusChoices.pending)
        )

    def handle(self, *args, **options):
        self.queue = options.get("queue", None)

        logger_name = options.get("logger_name", None)
        if logger_name is not None:
            self.LOGGER = logging.getLogger(logger_name)
            print("set custom logger")

        while True:
            try:
                jobs = self._mark_hanging_jobs_as_pending()
                break
            except DatabaseError:
                self.LOGGER.error(
                    "DatabaseError occurred when getting jobs with hanging status."
                )
                time.sleep(30)
                continue

        self.LOGGER.info(f"jobs with status In Progress on worker start: {jobs}")

        asyncio.run(self._asyncio_main_func())

        time.sleep(settings.JOB_POLLER_TIMEOUT_BEFORE_KILLED)

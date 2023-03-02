from django.contrib import admin
from simple_jobs.models import Job, JobResult


class JobResultAdmin(admin.StackedInline):
    model = JobResult


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    inlines = [JobResultAdmin]
    list_display = (
        "id",
        "function_name",
        "function_arguments",
        "is_one_off",
        "status",
        "periodic_schedule",
        "last_run_at",
        "is_scheduled_for_retry",
        "retry_times",
        "disabled",
    )

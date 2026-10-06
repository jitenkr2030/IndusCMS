import time

from django.core.management.base import BaseCommand

from core.services.workflow_worker import (
    DEFAULT_LIMIT,
    get_worker_id,
    process_pending,
)


class Command(BaseCommand):
    help = "Process queued IndusCMS workflow actions."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Process the queue once and exit.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=DEFAULT_LIMIT,
            help="Maximum actions per polling cycle.",
        )
        parser.add_argument(
            "--sleep",
            type=int,
            default=5,
            help="Seconds between polling cycles.",
        )

    def handle(self, *args, **options):
        limit = max(options["limit"], 1)
        sleep_seconds = max(options["sleep"], 1)
        once = options["once"]
        worker_id = get_worker_id()

        self.stdout.write(
            self.style.SUCCESS(
                f"Workflow worker started: {worker_id}"
            )
        )

        while True:
            results = process_pending(
                limit=limit,
                worker_id=worker_id,
            )

            if results:
                self.stdout.write(
                    f"Processed {len(results)} execution(s)."
                )

            if once:
                break

            time.sleep(sleep_seconds)

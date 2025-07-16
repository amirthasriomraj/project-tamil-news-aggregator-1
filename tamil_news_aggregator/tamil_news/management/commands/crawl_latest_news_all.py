from django.core.management.base import BaseCommand
from django.core.management import call_command

class Command(BaseCommand):
    help = "Run all Latest News crawlers"

    def handle(self, *args, **options):
        crawlers = [
            'hindu_tamil_latest_news'
            'puthiyathalaimurai_latest_news',
            'news18_tamil_latest_news',
        ]

        for crawler in crawlers:
            self.stdout.write(self.style.NOTICE(f"🚀 Running {crawler}..."))
            try:
                call_command(crawler)
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"❌ Failed: {crawler} → {e}"))

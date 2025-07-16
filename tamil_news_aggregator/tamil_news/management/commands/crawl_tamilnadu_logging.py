import asyncio
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command

# 🔧 Setup Logging
LOG_FILE = "tamilnadu_crawler_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class Command(BaseCommand):
    help = "Run all Tamilnadu news crawler scripts"

    def handle(self, *args, **options):
        logging.info("🚀 Starting Tamilnadu news Crawler Script")
        start_time = datetime.now()

        try:
            self.run_script("hindu_tamil_tamilnadu")
            self.run_script("bbc_tamil_tamilnadu")
            self.run_script("dinathanthi_tamilnadu")
            self.run_script("puthiyathalaimurai_tamilnadu")
            self.run_script("news18_tamil_tamilnadu")

        except Exception as e:
            logging.error(f"❌ Unexpected error during combined crawl: {str(e)}")

        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        logging.info(f"✅ Completed Tamilnadu news Crawl in {duration} seconds")

    def run_script(self, command_name):
        logging.info(f"▶ Running: {command_name}")
        try:
            call_command(command_name)
        except Exception as e:
            logging.error(f"❌ Error in {command_name}: {str(e)}")
            if any(keyword in str(e).lower() for keyword in ['403', 'denied', 'captcha', 'blocked']):
                logging.warning(f"⚠️ Possible IP block detected in {command_name}")

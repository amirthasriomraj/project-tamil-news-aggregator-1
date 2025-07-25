import asyncio
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.core.management import call_command

# 🔧 Setup Logging
LOG_FILE = "keyword_tamilnadu_crawler_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

class Command(BaseCommand):
    help = "Run all Tamilnadu keyword-based news crawlers for a list of Tamil keywords"

    def handle(self, *args, **options):
        keywords = ["ஸ்டாலின்", "சீமான்", "தவெக", "அதிமுக", "திமுக"]  # ✅ Update as needed

        logging.info("🚀 Starting ALL Tamilnadu keyword crawlers")
        start_time = datetime.now()

        try:
            for keyword in keywords:
                logging.info(f"\n📌 Processing keyword: {keyword}")
                self.run_keyword_crawlers(keyword)

        except Exception as e:
            logging.error(f"❌ Unexpected error during combined keyword crawl: {str(e)}")

        end_time = datetime.now()
        duration = (end_time - start_time).seconds
        logging.info(f"\n✅ Completed all keyword crawlers in {duration} seconds")

    def run_keyword_crawlers(self, keyword):
        scripts = [
            "key_hindu_tamil_tamilnadu",
            "key_bbc_tamil_tamilnadu",
            "key_dinathanthi_tamilnadu",
            "key_puthiyathalaimurai_tamilnadu",
            "key_news18_tamil_tamilnadu",
        ]

        for script in scripts:
            logging.info(f"▶ Running: {script} for keyword '{keyword}'")
            try:
                call_command(script, keyword=keyword)
            except Exception as e:
                logging.error(f"❌ Error in {script}: {str(e)}")
                if any(word in str(e).lower() for word in ['403', 'denied', 'captcha', 'blocked']):
                    logging.warning(f"⚠️ Possible IP block detected in {script}")

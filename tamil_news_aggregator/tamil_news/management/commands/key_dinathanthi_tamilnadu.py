from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails
import asyncio
from asgiref.sync import sync_to_async
from datetime import datetime
import pytz


class Command(BaseCommand):
    help = "Crawl DinaThanthi Tamilnadu News with Pagination and Optional Keyword Filter"

    def add_arguments(self, parser):
        parser.add_argument('--keyword', type=str, help='Filter articles by keyword (Tamil or English)')

    def handle(self, *args, **options):
        keyword = options.get("keyword")
        asyncio.run(self.crawl(keyword))

    def parse_date(self, date_str):
        if not date_str:
            return None
        try:
            dt = datetime.strptime(date_str.strip(), "%Y-%m-%d %H:%M:%S")
            return pytz.UTC.localize(dt)
        except Exception:
            return None

    async def crawl(self, keyword=None):
        website_name = "DinaThanthi"
        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        category = "Tamilnadu"

        max_pages = 80
        page_count = 0
        total_articles = 0
        matched_articles = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for page_num in range(1, max_pages + 1):
                page_count += 1
                url = f"https://www.dailythanthi.com/news/tamilnadu?page={page_num}"
                print(f"\n🌏 Scraping Page {page_count}: {url}")
                await page.goto(url, timeout=60000)

                news_blocks = await page.query_selector_all("div.ListingNewsWithMEDImage")
                num_articles = len(news_blocks)
                total_articles += num_articles

                print(f"Found {num_articles} articles on Page {page_count}")

                if num_articles == 0:
                    print("✅ No more articles found. Stopping.")
                    break

                for block in news_blocks:
                    try:
                        headline_el = await block.query_selector("h3")
                        title = (await headline_el.inner_text()).strip() if headline_el else "N/A"

                        if keyword and keyword not in title:
                            continue  # ✅ Skip non-matching articles

                        link_el = await block.query_selector("a[href]")
                        url = await link_el.get_attribute("href") if link_el else None
                        if url and not url.startswith("http"):
                            url = "https://www.dailythanthi.com" + url

                        img_el = await block.query_selector("img")
                        image_url = None
                        if img_el:
                            image_url = await img_el.get_attribute("data-src") or await img_el.get_attribute("src")

                        description_el = await block.query_selector("div")
                        description = (await description_el.inner_text()).strip() if description_el else None

                        datetime_el = await block.query_selector("span.convert-to-localtime")
                        date_str = await datetime_el.get_attribute("data-datestring") if datetime_el else None
                        published_time = self.parse_date(date_str)

                        await sync_to_async(NewsDetails.objects.get_or_create)(
                            website=website,
                            title=title,
                            article_url=url,
                            defaults={
                                'website_name': website.name,
                                'image_url': image_url,
                                'category': category,
                                'published_time': published_time,
                                'author': None,
                                'description': description,
                            }
                        )
                        matched_articles += 1
                        print(f"✅ {title}")

                    except Exception as e:
                        print(f"❌ Error parsing article: {e}")

            await browser.close()

        print(
            f"\n✅ Crawling Finished.\n"
            f"Total Pages Crawled: {page_count}\n"
            f"Total Articles Found: {total_articles}\n"
            f"✅ Total Articles Crawled (Matching Keyword): {matched_articles}"
        )

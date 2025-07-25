from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails
import asyncio
from asgiref.sync import sync_to_async
from datetime import datetime
import pytz


class Command(BaseCommand):
    help = "Crawl BBC Tamil Tamilnadu News with Pagination and Optional Keyword"

    def add_arguments(self, parser):
        parser.add_argument('--keyword', type=str, help='Filter articles by keyword (Tamil or English)')

    def handle(self, *args, **options):
        keyword = options.get("keyword")
        asyncio.run(self.crawl(keyword))

    async def crawl(self, keyword=None):
        website_name = "BBC Tamil"
        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        category = "Tamilnadu"

        max_pages = 15
        page_count = 0
        total_articles = 0
        matched_articles = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for page_num in range(1, max_pages + 1):
                page_count += 1
                url = f"https://www.bbc.com/tamil/topics/c6vzyv6g7yrt?page={page_num}"
                print(f"\n🌏 Scraping Page {page_count}: {url}")
                await page.goto(url, timeout=60000)

                articles = await page.query_selector_all("li.bbc-t44f9r")
                num_articles = len(articles)
                total_articles += num_articles

                print(f"Found {num_articles} articles on Page {page_count}")

                if num_articles == 0:
                    print("✅ No more articles found. Stopping.")
                    break

                for article in articles:
                    try:
                        title_el = await article.query_selector("h2")
                        title = (await title_el.inner_text()).strip() if title_el else "N/A"

                        # ✅ Skip if keyword is given and not matched in title
                        if keyword and keyword not in title:
                            continue

                        link_el = await title_el.query_selector("a") if title_el else None
                        url = await link_el.get_attribute("href") if link_el else None
                        if url and not url.startswith("http"):
                            url = "https://www.bbc.com" + url

                        image_el = await article.query_selector("img")
                        image_url = await image_el.get_attribute("src") if image_el else None

                        time_el = await article.query_selector("time")
                        time_text = await time_el.get_attribute("datetime") if time_el else None

                        # ✅ Convert published time to timezone-aware datetime
                        published_time = None
                        if time_text:
                            try:
                                published_time = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
                                published_time = published_time.astimezone(pytz.UTC)
                            except Exception:
                                published_time = None

                        # ✅ Save only if keyword matched or not given
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
                                'description': None,
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

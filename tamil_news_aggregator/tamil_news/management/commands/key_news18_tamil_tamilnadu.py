from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails
import asyncio
from asgiref.sync import sync_to_async


class Command(BaseCommand):
    help = "Crawl News18 Tamil - Tamilnadu Category using pagination and keyword filter"

    def add_arguments(self, parser):
        parser.add_argument("--keyword", type=str, required=True, help="Keyword to filter Tamil news titles")

    def handle(self, *args, **options):
        keyword = options["keyword"]
        asyncio.run(self.crawl(keyword))

    async def crawl(self, keyword):
        website_name = "News18 Tamil"
        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        category = "Tamilnadu"

        max_pages = 25
        total_articles = 0
        total_matching = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for page_num in range(1, max_pages + 1):
                if page_num == 1:
                    url = "https://tamil.news18.com/tamil-nadu/"
                else:
                    url = f"https://tamil.news18.com/tamil-nadu/page-{page_num}/"

                print(f"\n🌐 Scraping Page {page_num}: {url}")
                await page.goto(url, timeout=60000)

                news_items = await page.query_selector_all("li.jsx-d0e08582aab1ee73")
                print(f"🔎 Found {len(news_items)} articles on page {page_num}")

                if not news_items:
                    print("✅ No more articles found. Stopping.")
                    break

                for item in news_items:
                    try:
                        # Title
                        title_el = await item.query_selector("figcaption")
                        title = (await title_el.inner_text()).strip() if title_el else None

                        if not title or keyword not in title:
                            continue

                        # URL
                        link_el = await item.query_selector("a[href]")
                        relative_url = await link_el.get_attribute("href") if link_el else None
                        full_url = f"https://tamil.news18.com{relative_url}" if relative_url else None

                        # Image
                        img_el = await item.query_selector("img")
                        image_url = await img_el.get_attribute("src") if img_el else None

                        await sync_to_async(NewsDetails.objects.get_or_create)(
                            website=website,
                            title=title,
                            article_url=full_url,
                            defaults={
                                'website_name': website.name,
                                'image_url': image_url,
                                'category': category,
                                'published_time': None,
                                'author': None,
                                'description': None,
                            }
                        )
                        print(f"✅ {title}")
                        total_matching += 1

                    except Exception as e:
                        print(f"❌ Error parsing article: {e}")

                total_articles += len(news_items)

            await browser.close()

        print(
            f"\n✅ Crawling Finished.\nTotal Pages Crawled: {max_pages}\nTotal Articles Found: {total_articles}\n✅ Total Articles Crawled (Matching Keyword): {total_matching}"
        )

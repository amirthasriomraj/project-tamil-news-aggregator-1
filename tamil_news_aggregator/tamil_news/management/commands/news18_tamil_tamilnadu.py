from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails
import asyncio
from asgiref.sync import sync_to_async


class Command(BaseCommand):
    help = "Crawl News18 Tamil - Tamilnadu Category with Load More button handling"

    def handle(self, *args, **kwargs):
        asyncio.run(self.crawl())

    async def crawl(self):
        website_name = "News18 Tamil"
        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        category = "Tamilnadu"

        max_clicks = 10
        clicks_done = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            url = "https://tamil.news18.com/tamil-nadu/"
            print(f"\n🌐 Opening {url}")
            await page.goto(url, timeout=60000)

            # Click 'Load More' button repeatedly
            while clicks_done < max_clicks:
                print(f"🔄 Click {clicks_done + 1}/{max_clicks} on 'Load More'...")

                load_more = await page.query_selector('button.Load_more')  # ✅ Correct for India
                if load_more:
                    await load_more.click()
                    await page.wait_for_timeout(2000)
                    clicks_done += 1
                else:
                    print("✅ No more 'Load More' button found. Stopping.")
                    break

            news_cards = await page.query_selector_all("li.jsx-c82f6dc2e757e0b3")
            print(f"\n📰 Found {len(news_cards)} articles after scrolling.")

            total_articles = 0

            for card in news_cards:
                try:
                    # Title
                    title_el = await card.query_selector("figcaption")
                    title = (await title_el.inner_text()).strip() if title_el else "N/A"

                    # URL
                    link_el = await card.query_selector("a[href]")
                    url = await link_el.get_attribute("href") if link_el else None
                    if url and not url.startswith("http"):
                        url = "https://tamil.news18.com" + url

                    # Image
                    img_el = await card.query_selector("img")
                    image_url = None
                    if img_el:
                        img_src = await img_el.get_attribute("src")
                        if img_src:
                            image_url = img_src.strip()

                    await sync_to_async(NewsDetails.objects.get_or_create)(
                        website=website,
                        title=title,
                        article_url=url,
                        defaults={
                            'website_name': website.name,
                            'image_url': image_url,
                            'category': category,
                            'published_time': None,  # Published time not available here
                            'author': None,
                            'description': None,
                        }
                    )
                    print(f"✅ {title}")
                    total_articles += 1

                except Exception as e:
                    print(f"❌ Error parsing article: {e}")

            await browser.close()

        print(
            f"\n✅ Crawling Finished.\nTotal Load More Clicks Performed: {clicks_done}\nTotal Articles Found: {total_articles}"
        )

from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails
import asyncio
from asgiref.sync import sync_to_async
from datetime import datetime
from django.utils import timezone


class Command(BaseCommand):
    help = "Crawl Puthiyathalaimurai Latest News"

    def handle(self, *args, **kwargs):
        asyncio.run(self.crawl())

    def parse_datetime(self, datetime_str):
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '')).replace(microsecond=0)
            # ✅ Convert to timezone-aware datetime
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            return dt
        except Exception:
            return None

    async def crawl(self):
        website_name = "Puthiyathalaimurai"
        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        category = "Latest News"

        max_scrolls = 20
        scrolls_done = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            url = "https://www.puthiyathalaimurai.com/collection/lastpublished"
            print(f"\n🌐 Opening {url}")
            await page.goto(url)

            previous_height = await page.evaluate("document.body.scrollHeight")

            while scrolls_done < max_scrolls:
                print(f"🔄 Scroll {scrolls_done + 1}/{max_scrolls}...")

                await page.mouse.wheel(0, 3000)
                await page.wait_for_timeout(2000)

                current_height = await page.evaluate("document.body.scrollHeight")

                if current_height == previous_height:
                    read_more = await page.query_selector('div[data-test-id="load-more"]')
                    if read_more:
                        print("🖱️ Clicking 'Read More' button...")
                        await read_more.click()
                        await page.wait_for_timeout(2000)
                        current_height = await page.evaluate("document.body.scrollHeight")
                        if current_height == previous_height:
                            print("✅ No more content after 'Read More'. Stopping.")
                            break
                        else:
                            previous_height = current_height
                            scrolls_done += 1
                            continue
                    else:
                        print("✅ No more content. No 'Read More' button found. Stopping.")
                        break

                previous_height = current_height
                scrolls_done += 1

            news_cards = await page.query_selector_all("div.four-col-five-stories-m_card__2lzhH")
            print(f"\n📰 Found {len(news_cards)} articles after scrolling.")

            for card in news_cards:
                try:
                    title_el = await card.query_selector("h6")
                    title = (await title_el.inner_text()).strip() if title_el else "N/A"

                    link_el = await card.query_selector("a[href]")
                    url = await link_el.get_attribute("href") if link_el else None
                    if url and not url.startswith("http"):
                        url = "https://www.puthiyathalaimurai.com" + url

                    img_el = await card.query_selector("img")
                    image_url = None
                    if img_el:
                        img_url = await img_el.get_attribute("src")
                        if img_url:
                            image_url = img_url if img_url.startswith("http") else "https:" + img_url

                    author_el = await card.query_selector("div.author-name")
                    author = (await author_el.inner_text()).strip() if author_el else None

                    time_el = await card.query_selector("time")
                    datetime_str = await time_el.get_attribute("datetime") if time_el else None
                    published_time = self.parse_datetime(datetime_str) if datetime_str else None

                    desc_el = await card.query_selector("div.read-time-m_read-time-wrapper__3GyC_")
                    description = (await desc_el.inner_text()).strip() if desc_el else title

                    await sync_to_async(NewsDetails.objects.get_or_create)(
                        website=website,
                        title=title,
                        article_url=url,
                        defaults={
                            'website_name': website.name,
                            'image_url': image_url,
                            'category': category,
                            'published_time': published_time,
                            'author': author,
                            'description': description,
                        }
                    )
                    print(f"✅ {title}")

                except Exception as e:
                    print(f"❌ Error parsing article: {e}")

            await browser.close()

        print(
            f"\n✅ Crawling Finished.\nTotal Scrolls/Loads Performed: {scrolls_done}\nTotal Articles Found: {len(news_cards)}"
        )

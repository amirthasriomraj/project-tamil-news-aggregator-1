from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails
import asyncio
from asgiref.sync import sync_to_async
from datetime import datetime
from django.utils import timezone


def parse_date(text):
    if not text:
        return None

    tamil_to_english_months = {
        "ஜனவரி": "January", "பிப்ரவரி": "February", "மார்ச்": "March",
        "ஏப்ரல்": "April", "மே": "May", "ஜூன்": "June", "ஜூலை": "July",
        "ஆகஸ்ட்": "August", "செப்டம்பர்": "September", "அக்டோபர்": "October",
        "நவம்பர்": "November", "டிசம்பர்": "December"
    }

    for tamil, eng in tamil_to_english_months.items():
        text = text.replace(tamil, eng)

    try:
        naive_date = datetime.strptime(text.strip(), "%d %B, %Y")
        return timezone.make_aware(naive_date)
    except ValueError:
        try:
            naive_date = datetime.strptime(text.strip(), "%d %b, %Y")
            return timezone.make_aware(naive_date)
        except Exception:
            return None


class Command(BaseCommand):
    help = "Crawl Hindu Tamil Latest News with Pagination"

    def handle(self, *args, **kwargs):
        asyncio.run(self.crawl())

    async def crawl(self):
        website_name = "Hindu Tamil"
        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        category = "Latest News"

        max_pages = 10
        page_count = 0
        total_articles = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for page_num in range(1, max_pages + 1):
                page_count += 1

                url = "https://www.hindutamil.in/latest-news-tamil" if page_num == 1 \
                    else f"https://www.hindutamil.in/latest-news-tamil/{page_num}"

                print(f"\n📰 Scraping Page {page_count}: {url}")
                await page.goto(url, timeout=60000)  # Increased timeout

                articles = await page.query_selector_all("div.card-outer._shareContainer")
                num_articles = len(articles)
                total_articles += num_articles

                print(f"Found {num_articles} articles on Page {page_count}")

                if num_articles == 0:
                    print("✅ No more articles found. Stopping.")
                    break

                for article in articles:
                    try:
                        title_el = await article.query_selector("p.card-text")
                        title = (await title_el.inner_text()).strip() if title_el else "N/A"

                        url_el = await article.query_selector("a[href]")
                        url = await url_el.get_attribute("href") if url_el else ""
                        if url and not url.startswith("http"):
                            url = "https://www.hindutamil.in" + url

                        image_el = await article.query_selector("img")
                        image_url = await image_el.get_attribute("src") if image_el else None

                        author_tag = await article.query_selector(".card-bottom span")
                        author = (await author_tag.inner_text()).strip() if author_tag else None

                        date_tag = await article.query_selector(".card-bottom .date")
                        date_text = (await date_tag.inner_text()).strip() if date_tag else None

                        published_time = parse_date(date_text) if date_text else None

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
                                'description': None,
                            }
                        )
                        print(f"✅ {title}")

                    except Exception as e:
                        print(f"❌ Error parsing article: {e}")

            await browser.close()

        print(
            f"\n✅ Crawling Finished.\nTotal Pages Crawled: {page_count}\nTotal Articles Found: {total_articles}"
        )

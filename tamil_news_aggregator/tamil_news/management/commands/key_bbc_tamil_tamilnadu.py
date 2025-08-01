from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from tamil_news.models import Websites, NewsDetails, Keyword
import asyncio
from asgiref.sync import sync_to_async
from datetime import datetime
from django.utils import timezone


class Command(BaseCommand):
    help = "Crawl BBC Tamil Tamilnadu News and match with DB keywords"

    def handle(self, *args, **kwargs):
        asyncio.run(self.crawl())

    async def crawl(self):
        website_name = "BBC Tamil"
        category = "Tamilnadu"

        website, _ = await sync_to_async(Websites.objects.get_or_create)(name=website_name)
        keywords = await sync_to_async(list)(Keyword.objects.values_list("name", flat=True))

        max_pages = 1
        page_count = 0
        total_articles = 0
        crawled_articles = 0

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            for page_num in range(1, max_pages + 1):
                page_count += 1
                url = f"https://www.bbc.com/tamil/topics/c6vzyv6g7yrt?page={page_num}"
                print(f"\n🌍 Scraping Page {page_count}: {url}")
                await page.goto(url, timeout=60000)

                articles = await page.query_selector_all("li.bbc-t44f9r")
                num_articles = len(articles)
                total_articles += num_articles

                print(f"Found {num_articles} articles on Page {page_count}")
                if num_articles == 0:
                    break

                for article in articles:
                    try:
                        title_el = await article.query_selector("h2")
                        title = (await title_el.inner_text()).strip() if title_el else "N/A"

                        link_el = await title_el.query_selector("a") if title_el else None
                        url = await link_el.get_attribute("href") if link_el else ""
                        if url and not url.startswith("http"):
                            url = "https://www.bbc.com" + url

                        image_el = await article.query_selector("img")
                        image_url = await image_el.get_attribute("src") if image_el else None

                        time_el = await article.query_selector("time")
                        time_text = await time_el.get_attribute("datetime") if time_el else None

                        published_time = None
                        if time_text:
                            try:
                                published_time = datetime.fromisoformat(time_text.replace("Z", "+00:00"))
                                published_time = timezone.make_aware(published_time)
                            except Exception:
                                published_time = None

                        # ✅ Open article and extract full description
                        article_page = await browser.new_page()
                        await article_page.goto(url, timeout=60000)

                        desc_elements = await article_page.query_selector_all("div.bbc-19j92fr p.bbc-iy8ud2")
                        description_parts = [await el.inner_text() for el in desc_elements if await el.inner_text()]
                        description = "\n".join([text.strip() for text in description_parts]).strip()
                        await article_page.close()

                        if not description:
                            continue

                        # ✅ Match keywords
                        matched_keywords = [kw for kw in keywords if kw in title or kw in description]
                        if not matched_keywords:
                            continue

                        news_obj, created = await sync_to_async(NewsDetails.objects.get_or_create)(
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

                        for kw in matched_keywords:
                            keyword_obj = await sync_to_async(Keyword.objects.get)(name=kw)
                            await sync_to_async(news_obj.keywords.add)(keyword_obj)

                        crawled_articles += 1
                        print(f"✅ {title}")

                    except Exception as e:
                        print(f"❌ Error: {e}")

            await browser.close()

        print(
            f"\n✅ Crawling Finished.\n"
            f"Total Pages Crawled: {page_count}\n"
            f"Total Articles Found: {total_articles}\n"
            f"✅ Total Articles Crawled (keyword matched): {crawled_articles}"
        )

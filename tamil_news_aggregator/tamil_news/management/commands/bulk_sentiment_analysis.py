from django.core.management.base import BaseCommand
from tamil_news.models import NewsDetails, SentimentResults
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from django.utils import timezone
import torch
import torch.nn.functional as F


class Command(BaseCommand):
    help = "Perform sentiment analysis on existing NewsDetails and store in SentimentResults"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE("🔍 Loading sentiment model..."))
        tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
        model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

        existing_ids = set(SentimentResults.objects.values_list("news_id", flat=True))
        news_to_process = NewsDetails.objects.exclude(id__in=existing_ids)

        self.stdout.write(f"📰 {news_to_process.count()} news entries to process")

        label_map = {
            0: "negative",
            1: "negative",
            2: "neutral",
            3: "positive",
            4: "positive"
        }

        for news in news_to_process:
            try:
                inputs = tokenizer(news.title, return_tensors="pt", truncation=True, padding=True)
                with torch.no_grad():
                    outputs = model(**inputs)
                    scores = F.softmax(outputs.logits, dim=1)[0]
                    predicted_class = torch.argmax(scores).item()

                sentiment_label = label_map.get(predicted_class, "neutral")
                sentiment_score = round(scores[predicted_class].item(), 3)

                SentimentResults.objects.create(
                    news=news,
                    sentiment_label=sentiment_label,
                    sentiment_score=sentiment_score,
                    website_name=news.website_name,
                    category=news.category,
                    processed_at=timezone.now()
                )

                self.stdout.write(self.style.SUCCESS(f"✅ Processed: {news.title[:60]}... → {sentiment_label}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error processing: {news.title[:60]}... → {e}"))

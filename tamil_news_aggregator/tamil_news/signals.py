from django.db.models.signals import post_save
from django.dispatch import receiver
from tamil_news.models import NewsDetails, SentimentResults
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from django.utils import timezone
import torch.nn.functional as F

# Load model/tokenizer only once
tokenizer = AutoTokenizer.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")
model = AutoModelForSequenceClassification.from_pretrained("nlptown/bert-base-multilingual-uncased-sentiment")

@receiver(post_save, sender=NewsDetails)
def analyze_sentiment(sender, instance, created, **kwargs):
    if not created:
        return

    # Check if sentiment already exists
    if SentimentResults.objects.filter(news=instance).exists():
        return

    # Analyze sentiment
    text = instance.title
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
        scores = F.softmax(outputs.logits, dim=1)[0]
        predicted_class = torch.argmax(scores).item()

    label_map = {
        0: "negative",
        1: "negative",
        2: "neutral",
        3: "positive",
        4: "positive"
    }
    sentiment_label = label_map.get(predicted_class, "neutral")
    sentiment_score = round(scores[predicted_class].item(), 3)

    # Create only if not exists
    SentimentResults.objects.get_or_create(
        news=instance,
        defaults={
            'sentiment_label': sentiment_label,
            'sentiment_score': sentiment_score,
            'website_name': instance.website_name,
            'category': instance.category,
            'processed_at': timezone.now()
        }
    )

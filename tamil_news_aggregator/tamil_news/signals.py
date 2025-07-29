from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from tamil_news.models import NewsDetails, SentimentResults, Keyword
from transformers import pipeline

import re

# Load sentiment analysis model
model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
sentiment_pipeline = pipeline("sentiment-analysis", model=model_name)

# Sentence extractor: Extracts 1 sentence before and after the matched keyword sentence
def extract_relevant_sentences(text: str, keyword: str, window: int = 1):
    sentences = re.split(r'[.!?।]', text)  # basic sentence split, customize if needed
    matched = []

    for i, sentence in enumerate(sentences):
        if keyword in sentence:
            start = max(i - window, 0)
            end = min(i + window + 1, len(sentences))
            matched = sentences[start:end]
            break  # Only use first match

    return ' '.join(matched).strip() if matched else None

@receiver(post_save, sender=NewsDetails)
def analyze_sentiment_per_keyword(sender, instance, created, **kwargs):
    if not created or not instance.description:
        return

    description = instance.description
    all_keywords = Keyword.objects.all()

    for keyword in all_keywords:
        keyword_text = keyword.name.strip()

        # Extract focused context around the keyword
        context = extract_relevant_sentences(description, keyword_text, window=1)
        if not context:
            continue  # Keyword not present or no usable context

        try:
            result = sentiment_pipeline(context)[0]  # Example: {'label': 'POSITIVE', 'score': 0.85}

            label = result['label'].lower()  # 'positive', 'neutral', or 'negative'
            score = result['score']

            positive_score = score if label == 'positive' else 0
            negative_score = score if label == 'negative' else 0
            neutral_score = score if label == 'neutral' else 0

            SentimentResults.objects.update_or_create(
                news=instance,
                keyword=keyword,
                defaults={
                    'title': instance.title,
                    'website_name': instance.website_name,
                    'category': instance.category,
                    'processed_at': timezone.now(),
                    'sentiment_label': label,
                    'sentiment_score': score,
                    'positive_score': positive_score,
                    'negative_score': negative_score,
                    'neutral_score': neutral_score,
                }
            )

        except Exception as e:
            print(f"❌ Error analyzing keyword '{keyword_text}': {e}")

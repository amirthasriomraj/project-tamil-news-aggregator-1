from django.db.models.signals import post_save
from django.dispatch import receiver
from tamil_news.models import NewsDetails, Keyword, SentimentResults
from transformers import pipeline
from django.utils import timezone
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

# Load model and tokenizer
MODEL_NAME = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
labels = ['negative', 'neutral', 'positive']

# Constants
MAX_TOKENS = 512
CHUNK_CHAR_SIZE = 400  # safe size for tokenizer to avoid token overflow
OVERLAP = 100

@receiver(post_save, sender=NewsDetails)
def analyze_sentiment_per_keyword(sender, instance, created, **kwargs):
    if not created or not instance.description:
        return

    description = instance.description
    title = instance.title or ""
    keywords = Keyword.objects.all()

    for keyword in keywords:
        keyword_text = keyword.name

        if keyword_text not in description:
            continue

        # Split the description into chunks with overlap
        chunks = []
        text_len = len(description)
        i = 0
        while i < text_len:
            chunk = description[i:i+CHUNK_CHAR_SIZE]
            if keyword_text in chunk:
                chunks.append(chunk)
            i += CHUNK_CHAR_SIZE - OVERLAP

        if not chunks:
            print(f"⚠️ Skipped '{keyword_text}' — not found in any chunk")
            continue

        # Collect scores across chunks
        pos_scores, neg_scores, neu_scores = [], [], []

        for chunk in chunks:
            inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=MAX_TOKENS)
            with torch.no_grad():
                outputs = model(**inputs)
                scores = torch.nn.functional.softmax(outputs.logits, dim=1).numpy()[0]
                neg_scores.append(scores[0])
                neu_scores.append(scores[1])
                pos_scores.append(scores[2])

        # Average all scores
        avg_neg = float(np.mean(neg_scores))
        avg_neu = float(np.mean(neu_scores))
        avg_pos = float(np.mean(pos_scores))

        score_dict = {'negative': avg_neg, 'neutral': avg_neu, 'positive': avg_pos}
        final_label = max(score_dict, key=score_dict.get)
        final_score = score_dict[final_label]

        # Save to DB
        try:
            SentimentResults.objects.update_or_create(
                news=instance,
                keyword=keyword,
                defaults={
                    'title': title,
                    'website_name': instance.website_name,
                    'category': instance.category,
                    'processed_at': timezone.now(),
                    'sentiment_label': final_label,
                    'sentiment_score': final_score,
                    'positive_score': avg_pos,
                    'negative_score': avg_neg,
                    'neutral_score': avg_neu,
                }
            )
            print(f"✅ Saved sentiment for keyword '{keyword_text}' → {final_label} ({final_score:.3f})")
        except Exception as e:
            print(f"❌ DB save failed for keyword '{keyword_text}': {e}")

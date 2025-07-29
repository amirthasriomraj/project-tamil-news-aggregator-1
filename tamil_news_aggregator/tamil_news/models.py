from django.db import models
from django.utils import timezone


class Websites(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        db_table = 'websites'

    def __str__(self):
        return self.name


class Keyword(models.Model):
    #name = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)


    class Meta:
        db_table = 'keywords'

    def __str__(self):
        return self.name


class NewsDetails(models.Model):
    website = models.ForeignKey(Websites, models.DO_NOTHING, blank=True, null=True)
    website_name = models.CharField(max_length=255, blank=True, null=True)
    title = models.TextField()
    article_url = models.TextField(null=False, blank=False)
    image_url = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    published_time = models.DateTimeField(blank=True, null=True)
    language = models.CharField(max_length=100, blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    keywords = models.ManyToManyField(Keyword, related_name='news')

    class Meta:
        db_table = 'news_details'
        constraints = [
            models.UniqueConstraint(
                fields=['website', 'category', 'article_url'],
                name='unique_website_category_url'
            )
        ]

    def __str__(self):
        return self.title


class SentimentResults(models.Model):
    news = models.ForeignKey(NewsDetails, on_delete=models.CASCADE)
    #keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE)
    keyword = models.ForeignKey(Keyword, on_delete=models.CASCADE, null=True, blank=True)
    #title = models.TextField()
    title = models.TextField(null=True, blank=True)
    sentiment_label = models.CharField(max_length=50)
    sentiment_score = models.FloatField()
    #positive_score = models.FloatField()
    #negative_score = models.FloatField()
    #neutral_score = models.FloatField()
    positive_score = models.FloatField(null=True, blank=True)
    negative_score = models.FloatField(null=True, blank=True)
    neutral_score = models.FloatField(null=True, blank=True)
    website_name = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    processed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'sentiment_results'
        constraints = [
        models.UniqueConstraint(fields=['news', 'keyword'], name='unique_news_keyword')
    ]

    def __str__(self):
        return f"{self.news.title[:50]}... → {self.sentiment_label} ({self.sentiment_score})"

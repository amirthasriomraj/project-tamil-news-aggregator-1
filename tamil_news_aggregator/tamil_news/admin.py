from django.contrib import admin
from .models import Websites, NewsDetails, SentimentResults


@admin.register(Websites)
class WebsitesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(NewsDetails)
class NewsDetailsAdmin(admin.ModelAdmin):
    list_display = ('title', 'website_name', 'category', 'published_time')
    search_fields = ('title', 'description', 'website_name', 'category')
    list_filter = ('website_name', 'category', 'language')
    date_hierarchy = 'published_time'
    ordering = ('-published_time',)
    readonly_fields = ('published_time',)
    list_per_page = 25


@admin.register(SentimentResults)
class SentimentResultsAdmin(admin.ModelAdmin):
    list_display = ('news', 'sentiment_label', 'sentiment_score', 'category', 'processed_at')
    list_filter = ('sentiment_label', 'category')
    search_fields = ('news__title', 'sentiment_label')
    ordering = ('-processed_at',)
    date_hierarchy = 'processed_at'
    list_per_page = 25


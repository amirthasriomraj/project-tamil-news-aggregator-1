from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WebsiteViewSet,
    NewsDetailsViewSet,
    KeywordsViewSet,
    SentimentResultsViewSet,
    KeywordSentimentViewSet,
    CrawlKeywordTriggerView,
    news_list
)

router = DefaultRouter()
router.register(r'websites', WebsiteViewSet)
router.register(r'news', NewsDetailsViewSet)
router.register(r'keywords', KeywordsViewSet)
router.register(r'sentiment-results', SentimentResultsViewSet)
router.register(r'keyword-sentiment', KeywordSentimentViewSet, basename='keyword-sentiment')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/trigger-crawl/', CrawlKeywordTriggerView.as_view(), name='trigger-crawl'),
    path('news/', news_list, name='news_list'),
]

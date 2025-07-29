from django.urls import path, include
from rest_framework import routers
from tamil_news import views

router = routers.DefaultRouter()
router.register(r'websites', views.WebsiteViewSet)
router.register(r'news', views.NewsDetailsViewSet)
router.register(r'keyword-sentiment', views.KeywordSentimentViewSet, basename='keyword-sentiment')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/trigger-keyword-crawl/', views.CrawlKeywordTriggerView.as_view(), name='trigger-keyword-crawl'),
    path('news/', views.news_list, name='news-list'),
]

from django.urls import path, include
from .views import (
    news_list,
    WebsiteViewSet,
    NewsDetailsViewSet,
    KeywordSentimentViewSet
)
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'websites', WebsiteViewSet)
router.register(r'news', NewsDetailsViewSet)
router.register(r'keyword-sentiment', KeywordSentimentViewSet, basename='keyword-sentiment')

urlpatterns = [
    path('api/', include(router.urls)),
    path('news/', news_list, name='news_list'),
]

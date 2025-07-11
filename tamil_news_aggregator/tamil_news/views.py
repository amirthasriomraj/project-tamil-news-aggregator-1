from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils.dateparse import parse_date
from rest_framework import viewsets, filters

from .models import NewsDetails, Websites, SentimentResults
from .serializers import WebsiteSerializer, NewsDetailsSerializer


# DRF API Views
class WebsiteViewSet(viewsets.ModelViewSet):
    queryset = Websites.objects.all()
    serializer_class = WebsiteSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['id', 'name']


class NewsDetailsViewSet(viewsets.ModelViewSet):
    queryset = NewsDetails.objects.all()
    serializer_class = NewsDetailsSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'category', 'author', 'website__name']
    ordering_fields = ['published_time', 'id']


# Frontend View
def news_list(request):
    news = NewsDetails.objects.select_related("sentiment").order_by('-published_time', '-id')
    websites = Websites.objects.all()

    website_id = request.GET.get('website')
    category = request.GET.get('category')
    sentiment_label = request.GET.get('sentiment')
    search_query = request.GET.get('search')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if website_id:
        news = news.filter(website_id=website_id)

    if category:
        news = news.filter(category__icontains=category)

    if sentiment_label:
        news = news.filter(sentiment__sentiment_label=sentiment_label)

    if search_query and search_query.lower() != 'none':
        news = news.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(author__icontains=search_query)
        )

    if start_date and end_date:
        start = parse_date(start_date)
        end = parse_date(end_date)
        if start and end:
            news = news.filter(published_time__isnull=False)
            news = news.filter(published_time__date__range=(start, end))

    paginator = Paginator(news, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    categories = NewsDetails.objects.values_list('category', flat=True).distinct()
    sentiments = SentimentResults.objects.values_list('sentiment_label', flat=True).distinct()

    context = {
        'news_list': page_obj,
        'websites': websites,
        'categories': categories,
        'sentiments': sentiments,
        'website_id': website_id,
        'category': category,
        'sentiment_label': sentiment_label,
        'search_query': search_query,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'tamil_news/news_list.html', context)

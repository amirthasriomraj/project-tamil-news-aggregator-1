from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils.dateparse import parse_date
from datetime import datetime, timedelta

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action

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


# ✅ New API ViewSet for Keyword Sentiment
class KeywordSentimentViewSet(viewsets.ViewSet):
    def list(self, request):
        return Response({
            "message": "Use /api/keyword-sentiment/sentiment/?keyword=... to get sentiment scores."
        })

    @action(detail=False, methods=['get'], url_path='sentiment')
    def sentiment(self, request):
        keyword = request.GET.get('keyword')
        range_type = request.GET.get('range_type')  # daily, weekly, monthly
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not keyword:
            return Response({"error": "Keyword is required"}, status=status.HTTP_400_BAD_REQUEST)

        today = datetime.today().date()
        if range_type == 'daily':
            start = today
            end = today
        elif range_type == 'weekly':
            start = today - timedelta(days=7)
            end = today
        elif range_type == 'monthly':
            start = today - timedelta(days=30)
            end = today
        elif start_date and end_date:
            start = parse_date(start_date)
            end = parse_date(end_date)
        else:
            start = None
            end = None

        news_qs = NewsDetails.objects.filter(
            Q(title__icontains=keyword) | Q(description__icontains=keyword)
        )
        if start and end:
            news_qs = news_qs.filter(published_time__isnull=False)
            news_qs = news_qs.filter(published_time__date__range=(start, end))

        sentiments = SentimentResults.objects.filter(news__in=news_qs)

        label_counts = sentiments.values('sentiment_label').annotate(count=Count('id'))
        avg_score = sentiments.aggregate(avg=Avg('sentiment_score'))['avg'] or 0

        response_data = {
            "keyword": keyword,
            "time_range": f"{start} to {end}" if start and end else "All time",
            "sentiment_breakdown": {entry['sentiment_label']: entry['count'] for entry in label_counts},
            "average_score": round(avg_score, 3),
            "total_matches": sentiments.count()
        }

        return Response(response_data)


# Frontend View for /news/
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

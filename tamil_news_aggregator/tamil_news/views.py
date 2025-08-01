from django.shortcuts import render
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.utils.dateparse import parse_date
from datetime import timedelta, date
import subprocess
import json

from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action

from .serializers import (
    WebsiteSerializer,
    NewsDetailsSerializer,
    KeywordSerializer,
    SentimentResultsSerializer
)
from .models import NewsDetails, Websites, SentimentResults, Keyword


class KeywordsViewSet(viewsets.ModelViewSet):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['id', 'name']


class SentimentResultsViewSet(viewsets.ModelViewSet):
    queryset = SentimentResults.objects.all()
    serializer_class = SentimentResultsSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['sentiment_label', 'news__title', 'news__description']
    ordering_fields = ['processed_at', 'positive_score', 'negative_score', 'neutral_score']


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


class KeywordSentimentViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def sentiment(self, request):
        keyword_name = request.query_params.get("keyword")
        range_type = request.query_params.get("range_type", "daily")  # daily, weekly, monthly
        website = request.query_params.get("website")
        category = request.query_params.get("category")

        if not keyword_name:
            return Response({"error": "Missing 'keyword' parameter."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            keyword = Keyword.objects.get(name=keyword_name)
        except Keyword.DoesNotExist:
            return Response({"error": f"Keyword '{keyword_name}' not found."}, status=status.HTTP_404_NOT_FOUND)

        today = date.today()

        # Define date range
        if range_type == "daily":
            start_date = today
        elif range_type == "weekly":
            start_date = today - timedelta(days=7)
        elif range_type == "monthly":
            start_date = today - timedelta(days=30)
        else:
            return Response({"error": "Invalid 'range_type'. Use 'daily', 'weekly', or 'monthly'."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Base queryset
        sentiment_qs = SentimentResults.objects.filter(
            keyword=keyword,
            news__published_time__date__gte=start_date
        )

        # Apply filters using AND logic
        if website:
            sentiment_qs = sentiment_qs.filter(news__website__name__iexact=website)

        if category:
            sentiment_qs = sentiment_qs.filter(news__category__iexact=category)

        aggregate = sentiment_qs.aggregate(
            avg_positive=Avg("positive_score"),
            avg_negative=Avg("negative_score"),
            avg_neutral=Avg("neutral_score"),
            match_count=Count("id")
        )

        return Response({
            "keyword": keyword.name,
            "range_type": range_type,
            "start_date": start_date,
            "end_date": today,
            "avg_positive_score": round(aggregate["avg_positive"] or 0, 4),
            "avg_negative_score": round(aggregate["avg_negative"] or 0, 4),
            "avg_neutral_score": round(aggregate["avg_neutral"] or 0, 4),
            "match_count": aggregate["match_count"],
            "filtered_by": {
                "website": website or "N/A",
                "category": category or "N/A"
            }
        })



class CrawlKeywordTriggerView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data
        keywords = data.get("keywords", [])
        if not isinstance(keywords, list) or not keywords:
            return Response({"error": "Please provide a non-empty list of keywords."},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            subprocess.Popen(
                ['python', 'manage.py', 'crawl_key_tamilnadu_logging', json.dumps(keywords)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return Response({"status": "Crawling triggered successfully."})
        except Exception as e:
            return Response({"error": str(e)}, status=500)


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

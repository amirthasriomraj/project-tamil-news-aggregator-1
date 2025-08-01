from rest_framework import serializers
from .models import Websites, NewsDetails, Keyword, SentimentResults

class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Websites
        fields = '__all__'

class NewsDetailsSerializer(serializers.ModelSerializer):
    #website = serializers.StringRelatedField()
    class Meta:
        model = NewsDetails
        fields = '__all__'

class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = '__all__'

class SentimentResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SentimentResults
        fields = '__all__'


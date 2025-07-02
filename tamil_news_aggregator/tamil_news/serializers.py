from rest_framework import serializers
from .models import Websites, NewsDetails


class WebsiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Websites
        fields = '__all__'


class NewsDetailsSerializer(serializers.ModelSerializer):
    website = serializers.StringRelatedField()
    #website = WebsiteSerializer(read_only=True)


    class Meta:
        model = NewsDetails
        fields = '__all__'

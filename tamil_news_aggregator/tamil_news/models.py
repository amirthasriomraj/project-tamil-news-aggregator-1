# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.



from django.db import models


class Websites(models.Model):
    name = models.CharField(max_length=255, unique=True) 

    class Meta:
        db_table = 'websites'

    def __str__(self):
        return self.name


class NewsDetails(models.Model):
    website = models.ForeignKey(
        Websites, models.DO_NOTHING, blank=True, null=True
    )
    website_name = models.CharField(max_length=255, blank=True, null=True)
    title = models.TextField()
    article_url = models.TextField(null=False, blank=False) 
    image_url = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    published_time = models.DateTimeField(blank=True, null=True) 
    language = models.CharField(max_length=100, blank=True, null=True)
    author = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

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


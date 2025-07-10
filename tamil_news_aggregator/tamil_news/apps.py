# from django.apps import AppConfig


# class TamilNewsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'tamil_news'


from django.apps import AppConfig

class TamilNewsConfig(AppConfig):
    name = 'tamil_news'

    def ready(self):
        import tamil_news.signals

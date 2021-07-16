from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.db.utils import IntegrityError
from django.dispatch import receiver

from .models import Recipe, Individual

# Thanks to the wonderful blog post found here:
# https://lewiskori.com/blog/user-registration-and-authorization-on-a-django-api-with-djoser-and-json-web-tokens/
# Obviously, I repurposed the idea but for graphql jwt
# Also check out the docs on signals: https://docs.djangoproject.com/en/3.2/topics/signals/
@receiver(post_save, sender=get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if created:
        Individual.objects.create(user=instance)

# It seemed easier to resolve this here
# that urls have to be unique if they're not blank
@receiver(pre_save, sender=Recipe)
def url_unique_if_exists(sender, instance, **kwargs):
    if instance.url:
        _urls = [recipe.url for recipe in Recipe.objects.all()]
        if instance.url in _urls:
            raise IntegrityError("Duplicate Key: URL already exists")

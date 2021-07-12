from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Individual

# Thanks to the wonderful blog post found here:
# https://lewiskori.com/blog/user-registration-and-authorization-on-a-django-api-with-djoser-and-json-web-tokens/
# Obviously, I repurposed the idea but for graphql jwt
# Also check out the docs on signals: https://docs.djangoproject.com/en/3.2/topics/signals/
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Individual.objects.create(user=instance)
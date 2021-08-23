from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.db.utils import IntegrityError
from django.dispatch import receiver

from .models import (
    Recipe,
    RecipeStep,
    Individual,
    Group,
    GroupMeal,
    IndividualMeal
)

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
        for recipe in sender.objects.all():
            if instance.id != recipe.id and instance.url == recipe.url:
                raise IntegrityError(f"Duplicate Key: URL {instance.url} already exists")

# A recipe's URL cannot ever be updated
@receiver(pre_save, sender=Recipe)
def url_cannot_be_changed_on_update(sender, instance, **kwargs):
    # See if we're updating a recipe or not
    try:
        old_recipe = sender.objects.get(id=instance.id)
    # If it's a new recipe, let it go
    except:
        return
    # Only raise exception if the URL has changed
    if old_recipe.url != instance.url:
        raise IntegrityError("Recipe URL cannot be changed after creation")

# The order of the steps will be assigned by the database
# If the order has not been set already
@receiver(pre_save, sender=RecipeStep)
def step_order_assignment(sender, instance, **kwargs):
    # print(sender.objects.filter(recipe=instance.recipe))
    if not instance.order and instance.order != 0:
        existing_steps = sender.objects.filter(recipe=instance.recipe)
        if len(existing_steps) > 0:
            # Make the current order of steps a range
            taken_step_orders = [step.order for step in existing_steps]
            prev_step_order = 0
            # We loop through the whole array and make sure there are no missing numbers
            for cur_step_order in taken_step_orders:
                # If there is a missing number, the order will take that position
                # then exit the function - we have our answer
                if cur_step_order != prev_step_order + 1:
                    instance.order = prev_step_order + 1
                    return
                # If we don't have a missing number, we move up the previous number
                # Then continue with the next one
                prev_step_order = cur_step_order
        # This outcome means all the numbers are in order [1, 2, 3, etc.]
        # or an empty list []. Either way we want the same thing:
        # The order is put at the last index + 1 (1 for an empty list, 1 + n for the in order list)
        instance.order = len(existing_steps) + 1

# The order of the steps for a recipe should be unqiue integers
@receiver(pre_save, sender=RecipeStep)
def step_order_unique(sender, instance, **kwargs):
    if instance.order < 1 or instance.order % 1 != 0:
        raise IntegrityError("Step order must be an integer greater than or equal to 1")
    if instance.order in [step.order for step in sender.objects.filter(recipe=instance.recipe)]:
        raise IntegrityError(f"Duplicate Key: {sender.recipe} already has step in order {instance.order}")

# Meals should be unique for that individual/group at that time & day
@receiver(pre_save, sender=GroupMeal)
def meal_time_day_unique_for_group(sender, instance, **kwargs):
    if (instance.time, instance.day) in [
        (meal.time, meal.day) for meal in GroupMeal.objects.filter(group=instance.group)
    ]:
        raise IntegrityError(
            f"Duplicate Key: Meal already exists for {instance.group.name} for {instance.day} at {instance.time}")


@receiver(pre_save, sender=IndividualMeal)
def meal_time_day_unique_for_individual(sender, instance, **kwargs):
    if (instance.time, instance.day) in [
        (meal.time, meal.day) for meal in sender.objects.filter(individual=instance.individual)
    ]:
        raise IntegrityError(
            f"Duplicate Key: Meal already exists for {instance.individual.user.email} for {instance.day} at {instance.time}")

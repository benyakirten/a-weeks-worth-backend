from django.contrib import admin
from django.apps import apps
from django.contrib.auth.models import Group as DjangoGroup

from .models import (
    RecipeIngredient,
    RecipeStep,
    Recipe,
    GroupShoppingItem,
    GroupMeal,
    Group,
    IndividualShoppingItem,
    IndividualMeal,
    Individual
)

# ********* RECIPE *********
class RecipeIngredientInline(admin.StackedInline):
    model = RecipeIngredient
    extra = 1

class RecipeStepInline(admin.StackedInline):
    model = RecipeStep
    extra = 1

class RecipeAdmin(admin.ModelAdmin):
    fields = ['name', 'photo', 'url']
    inlines = [RecipeIngredientInline, RecipeStepInline]

# ********* GROUP *********
class GroupShoppingItemInline(admin.StackedInline):
    model = GroupShoppingItem
    extra = 1

class GroupMealsInline(admin.StackedInline):
    model = GroupMeal
    extra = 1

class GroupAdmin(admin.ModelAdmin):
    fields = ['name', 'members', 'join_requests']
    inlines = [GroupMealsInline, GroupShoppingItemInline]

# ********* INDIVIDUAL *********
class IndividualShoppingItemInline(admin.StackedInline):
    model = IndividualShoppingItem
    extra = 1

class IndividualMealInline(admin.StackedInline):
    model = IndividualMeal
    extra = 1

class IndividualAdmin(admin.ModelAdmin):
    fields = ['groups', 'group_requests']
    inlines = [IndividualMealInline, IndividualShoppingItemInline]

admin.site.register(Recipe, RecipeAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Individual, IndividualAdmin)
# The regular Django groups aren't used since we don't care about privileges
# other than the super user.
admin.site.unregister(DjangoGroup)

app = apps.get_app_config('graphql_auth')

for model_name, model in app.models.items():
    admin.site.register(model)
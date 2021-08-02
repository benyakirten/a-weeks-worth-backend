import copy

import graphene
from graphql_jwt.decorators import login_required

from utils.comparison import compare_as_key

from aww.models import (
    Individual,
    GroupShoppingItem,
    GroupMeal,
    Group,
    Recipe
)
from ..types import (
    GroupType,
    IndividualType,
    IngredientInputType,
    MealInputType
)


class CreateGroup(graphene.Mutation):
    """
    Create a group with a unique name.
    The first member of the group will be the logged-in user's individual.
    """
    class Arguments:
        name = graphene.String(required=True)

    individual = graphene.Field(IndividualType)
    group = graphene.Field(GroupType)

    @classmethod
    @login_required
    def mutate(cls, root, info, name):
        group = Group(name=name)
        group.save()
        individual = info.context.user.individual
        group.members.add(individual)
        individual.groups.add(group)
        return CreateGroup(individual=individual, group=group)


class UpdateGroup(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        name = graphene.String(required=False)
        shopping_list = graphene.List(IngredientInputType, required=False)
        meals = graphene.List(MealInputType, required=False)

    group = graphene.Field(GroupType)

    @classmethod
    @login_required
    def mutate(cls, root, info, id, name="", shopping_list=None, meals=None):
        try:
            group = Group.objects.get(id=id)
        except:
            raise Exception("No group found corresponding to that ID")
        if info.context.user not in [member.user for member in group.members.all()]:
            raise Exception("Only a member of a group can update the group")
        if name:
            group.name = name
            group.save()

        if shopping_list is not None:
            queryset = GroupShoppingItem.objects.filter(group=group)
            for item in queryset:
                item.delete()
            for item in shopping_list:
                group.groupshoppingitem_set.create(
                    name=item.name, quantity=item.quantity, unit=item.unit)
        if meals is not None:
            queryset = GroupMeal.objects.filter(group=group)
            for meal in queryset:
                meal.delete()
            meals.sort(key=compare_as_key)
            for meal in meals:
                # If there's a recipe and some text (note)
                if meal.recipeId and meal.text:
                    try:
                        # Try to get the recipe, put it in
                        _recipe = Recipe.objects.get(id=meal.recipeId)
                        group.groupmeal_set.create(
                            recipe=_recipe, text=meal.text, day=meal.day, time=meal.time)
                    except:
                        # If we fail: make it without the recipe
                        group.groupmeal_set.create(
                            text=meal.text, day=meal.day, time=meal.time)
                # If there's a recipe but no text (note)
                elif meal.recipeId and not meal.text:
                    try:
                        # Idem
                        _recipe = Recipe.objects.get(id=meal.recipeId)
                        group.groupmeal_set.create(
                            recipe=_recipe, day=meal.day, time=meal.time)
                    except:
                        # If there's no recipe and no text, then this isn't a meal
                        continue
                # If there's a text/note but there's no recipe
                elif not meal.recipeId and meal.text:
                    group.groupmeal_set.create(
                        text=meal.text, day=meal.day, time=meal.time)
                # If there's no recipe and no text, then this isn't a meal
        return UpdateGroup(group=group)


class DeleteGroup(graphene.Mutation):
    """
    Delete a group.
    Mutation requires that the logged-in user's individual is a member of said group.
    """
    class Arguments:
        id = graphene.ID(required=True)

    group = graphene.Field(GroupType)

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        try:
            group = Group.objects.get(id=id)
        except:
            raise Exception("No group found by that ID")
        if info.context.user not in [member.user for member in group.members.all()]:
            raise Exception("Only a member of a group can update the group")
        # Make sure all the users still in the group remove it
        if group.members:
            for member in group.members.all():
                member.groups.remove(group)
                member.save()
        _group = copy.copy(group)
        group.delete()
        return DeleteGroup(group=_group)

class Mutation(graphene.ObjectType):
    update_group = UpdateGroup.Field()
    create_group = CreateGroup.Field()
    delete_group = DeleteGroup.Field()
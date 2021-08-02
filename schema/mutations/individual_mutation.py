import graphene
from graphql_jwt.decorators import login_required

from utils.comparison import compare_as_key

from aww.models import (
    Group,
    IndividualShoppingItem,
    IndividualMeal,
    Individual,
    Recipe
)

from ..types import (
    GroupType,
    IndividualType,
    IngredientInputType,
    RecipeStepInputType,
    MealInputType
)


class UpdateIndividual(graphene.Mutation):
    """
    Update the individual with a new shopping list and/or meals.
    This mutation will delete all current shopping list items or meals if either of those values are provided.
    """
    class Arguments:
        shopping_list = graphene.List(IngredientInputType, required=False)
        meals = graphene.List(MealInputType, required=False)

    individual = graphene.Field(IndividualType)

    @classmethod
    @login_required
    def mutate(cls, root, info, shopping_list=None, meals=None):
        individual = info.context.user.individual
        if shopping_list is not None:
            queryset = IndividualShoppingItem.objects.filter(
                individual=individual)
            for item in queryset:
                item.delete()
            for item in shopping_list:
                individual.individualshoppingitem_set.create(
                    name=item.name, quantity=item.quantity, unit=item.unit)
        if meals is not None:
            queryset = IndividualMeal.objects.filter(individual=individual)
            for meal in queryset:
                meal.delete()
            meals.sort(key=compare_as_key)
            for meal in meals:
                if meal.recipeId and meal.text:
                    try:
                        # Try to get the recipe, put it in
                        _recipe = Recipe.objects.get(id=meal.recipeId)
                        individual.individualmeal_set.create(
                            recipe=_recipe, text=meal.text, day=meal.day, time=meal.time)
                    except:
                        # If we fail: make it without the recipe
                        individual.individualmeal_set.create(
                            text=meal.text, day=meal.day, time=meal.time)
                elif meal.recipeId and not meal.text:
                    try:
                        # Idem
                        _recipe = Recipe.objects.get(id=meal.recipeId)
                        individual.individualmeal_set.create(
                            recipe=_recipe, day=meal.day, time=meal.time)
                    except:
                        # If there's no recipe and no text, then this isn't a meal
                        continue
                elif not meal.recipeId and meal.text:
                    individual.individualmeal_set.create(
                        text=meal.text, day=meal.day, time=meal.time)
        return UpdateIndividual(individual=individual)

class RequestAccess(graphene.Mutation):
    """
    Request access to a group.
    An exception will be raised if the request has been made previously.
    """
    class Arguments:
        id = graphene.ID(required=True)
    
    individual = graphene.Field(IndividualType)
    success = graphene.Field(graphene.Boolean)

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        try:
            group = Group.objects.get(id=id)
        except:
            raise Exception("Group cannot be found with that ID")
        individual = info.context.user.individual
        if individual in group.join_requests.all() or group in individual.group_requests.all():
            raise Exception("User has already made a request to access that group")
        group.join_requests.add(individual)
        individual.group_requests.add(group)

        return RequestAccess(individual=individual, success=True)

class CancelRequest(graphene.Mutation):
    """
    Cancels a previously made request to be invited into a group
    Raises an exception if the request has not yet been made or was previously canceled
    """
    class Arguments:
        id = graphene.ID(required=True)

    individual = graphene.Field(IndividualType)
    success = graphene.Field(graphene.Boolean)

    @classmethod
    @login_required
    def mutate(cls, root, info, id):
        try:
            group = Group.objects.get(id=id)
        except:
            raise Exception("Group cannot be found with that ID")
        individual = info.context.user.individual
        if individual not in group.join_requests.all():
            raise Exception("User not within requests for group")
        if group not in individual.group_requests.all():
            raise Exception("Group not within requests made by user")
        group.join_requests.remove(individual)
        individual.group_requests.remove(group)

        return CancelRequest(individual=individual, success=True)

class InviteToGroup(graphene.Mutation):
    """
    Adds an individual to a group and the group to the individual's groups
    Logged in user must be in that group and the invited individual cannot be a part of the group.
    """
    class Arguments:
        invitedId = graphene.ID(required=True)
        groupId = graphene.ID(required=True)

    individual = graphene.Field(IndividualType)
    group = graphene.Field(GroupType)

    @classmethod
    @login_required
    def mutate(cls, root, info, invitedId, groupId):
        try:
            invited = Individual.objects.get(id=invitedId)
            group = Group.objects.get(id=groupId)
        except:
            raise Exception("Group and/or individual ID cannot be found")
        if info.context.user.individual not in group.members.all():
            raise Exception("Inviter must be a part of the group")
        if invited in group.members.all():
            raise Exception("Invited individual already in the group")
        
        # If there was a request, remove it now from both sides
        if group in invited.group_requests.all():
            invited.group_requests.remove(group)
        if invited in group.join_requests.all():
            group.join_requests.remove(invited)

        invited.groups.add(group)
        group.members.add(invited)

        return InviteToGroup(individual=invited, group=group)

class LeaveGroup(graphene.Mutation):
    """
    Removes the logged in user's individual from a group and remove that group from the individual's groups.
    Raises an exception if the user is not in the group
    """
    class Arguments:
        id = graphene.ID(required=False)
        name = graphene.String(required=False)

    individual = graphene.Field(IndividualType)

    @classmethod
    @login_required
    def mutate(cls, root, info, id="", name=""):
        if not id and not name:
            raise Exception("Either a group name or ID must be provided")
        if id and name:
            raise Exception("Both a group name and an ID cannot be provided")
        try:
            if name: group = Group.objects.get(name=name)
            if id: group = Group.objects.get(id=id)
        except:
            raise Exception("Group and/or individual ID cannot be found")

        individual = info.context.user.individual
        if individual not in group.members.all() or group not in individual.groups.all():
            raise Exception("User cannot leave group it is not in")

        individual.groups.remove(group)

        # If a group has lost its last member, delete it
        if len(group.members.all()) == 1:
            group.delete()
        else:
        # Otherwise just remove that individual from its members
            group.members.remove(individual)

        return LeaveGroup(individual=individual)

class Mutation(graphene.ObjectType):
    update_individual = UpdateIndividual.Field()
    request_access = RequestAccess.Field()
    cancel_request = CancelRequest.Field()
    invite_to_group = InviteToGroup.Field()
    leave_group = LeaveGroup.Field()

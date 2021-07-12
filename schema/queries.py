import graphene
from graphene_django import DjangoListField
from graphql_jwt.decorators import login_required, superuser_required

from aww.models import Individual, Group, Recipe

from .types import (
    RecipeStepType,
    RecipeIngredientType,
    RecipeType,
    GroupShoppingItemType,
    GroupMealType,
    GroupType,
    GroupsType,
    IndividualShoppingItemType,
    IndividualMealType,
    IndividualType
)

class LimitedIndividualType(graphene.ObjectType):
    """
    An individual type that only gives its id, groups, email and username.
    Used only in a superuser's query that gets all individuals. If recipe or
    meal information is needed, it can be accessed in the Django admin panel.
    """
    class Meta:
        model = Individual
        fields = ('id',)

    groups = graphene.List(GroupType)
    email = graphene.String()
    username = graphene.String()

    def resolve_groups(self, info):
        return self.groups.all()

    def resolve_email(self, info):
        return self.user.email

    def resolve_username(self, info):
        return self.user.username

class Query(graphene.ObjectType):
    recipes = DjangoListField(RecipeType)
    groups = DjangoListField(GroupsType)

    recipe = graphene.Field(RecipeType, id=graphene.ID(
        required=False), name=graphene.String(required=False))

    def resolve_recipe(root, info, id="", name=""):
        if not id and not name:
            raise Exception("ID or name must be provided")
        if id and name:
            raise Exception("Both ID and name cannot be provided")
        try:
            if id:
                return Recipe.objects.get(id=id)
            if name:
                return Recipe.objects.get(name=name)
        except:
            raise Exception("No recipe found by that id or name")
    
    recipe_urls = graphene.List(graphene.String)

    def resolve_recipe_urls(root, info):
        _recipes = Recipe.objects.all()
        return [recipe.url for recipe in _recipes]

    individual = graphene.Field(IndividualType, id=graphene.ID(
        required=False), email=graphene.String(required=False))

    # This same function is better done by the MeQuery.
    # That said, this is a function for a superuser to look for an individual
    @superuser_required
    def resolve_individual(root, info, id="", email=""):
        if not id and not email:
            raise Exception("ID or email must be provided")
        if id and email:
            raise Exception("Both ID and name cannot be provided")
        try:
            if id:
                _user = Individual.objects.get(id=id)
            if email:
                _individuals = Individual.objects.all()
                [_user] = [individualUser for individualUser in _individuals if individualUser.user.email == email]
            return _user
        except:
            raise Exception("No individual found by that id or email")

    all_individuals = graphene.List(LimitedIndividualType)

    @superuser_required
    def resolve_all_individuals(root, info):
        return Individual.objects.all()

    group = graphene.Field(GroupType, id=graphene.ID(
        required=False), name=graphene.String(required=False))

    # No idea why you'd ever need this query, given the MeQuery
    # But might as well get some experience
    @login_required
    def resolve_group(root, info, id="", name=""):
        if not id and not name:
            raise Exception("Id or name must be provided")
        try:
            if id:
                _group = Group.objects.get(id=id)
            if name:
                _group = Group.objects.get(name=name)
        except:
            raise Exception("No group found by that id or name")
        if info.context.user in [member.user for member in _group.members.all()]:
            return _group
        else:
            raise Exception(
                "Single group may only be queried by its members")

    my_groups = graphene.Field(graphene.List(GroupType))

    @login_required
    def resolve_my_groups(root, info):
        return info.context.user.individual.groups.all()
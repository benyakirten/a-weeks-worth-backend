import graphene
from graphene_django import DjangoObjectType

from aww.models import (
    GroupShoppingItem,
    GroupMeal,
    Group,
    IndividualShoppingItem,
    IndividualMeal,
    Individual,
    RecipeIngredient,
    RecipeStep,
    Recipe
)

# *** Query Types ***
# Recipe
class RecipeStepType(DjangoObjectType):
    """
    A step for a recipe with a step and an order
    The order is the order that the step comes in. It should be positive and grow linearly, but that constraint isn't enforced on the backend.
    """
    class Meta:
        model = RecipeStep
        fields = ('id', 'step', 'order')


class RecipeIngredientType(DjangoObjectType):
    """Ingredient for a recipe"""
    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'quantity', 'unit')


class RecipeType(DjangoObjectType):
    """
    Global recipe available to all users.
    Ingredients and the steps are resolved instead of their model's field names, recipeingredient_set and recipestep_set respectively
    """
    class Meta:
        model = Recipe
        fields = ('id', 'name', 'photo', 'url')

    # To make these fields more clear-cut instead of having to be called as
    # recipeingredient_set (recipeingredientSet) and recipestep_set (recipestepSet)
    ingredients = graphene.List(RecipeIngredientType)
    steps = graphene.List(RecipeStepType)

    def resolve_ingredients(self, info):
        return self.recipeingredient_set.all()

    def resolve_steps(self, info):
        return self.recipestep_set.all()

# Request
class RequestType(graphene.ObjectType):
    """Subtype not inherited from Django model to represent a request made by an individual to join a group, used both in the group's join_requests and the individual's group_requests"""
    id = graphene.ID()
    name = graphene.String()

# Group
class GroupShoppingItemType(DjangoObjectType):
    """Shopping Item based on the GroupShoppingItem"""
    class Meta:
        model = GroupShoppingItem
        fields = ('id', 'name', 'quantity', 'unit')


class GroupMealType(DjangoObjectType):
    """Meal based on the GroupMeal"""
    class Meta:
        model = GroupMeal
        fields = ('id', 'recipe', 'text', 'day', 'time')


class GroupsType(DjangoObjectType):
    """Publically available group item with limited information"""
    class Meta:
        model = Group
        fields = ('id', 'name')

    members = graphene.List(graphene.String)

    def resolve_members(self, info):
        _members = self.members.all()
        return [member.user.email for member in _members]


class GroupType(DjangoObjectType):
    """Group type that will only be available for members of a group."""
    class Meta:
        model = Group
        fields = ('id', 'name')

    members = graphene.List(graphene.String)
    requests = graphene.List(RequestType)
    shopping_list = graphene.List(GroupShoppingItemType)
    meals = graphene.List(GroupMealType)

    def resolve_members(self, info):
        _members = self.members.all()
        return [member.user.email for member in _members]

    def resolve_requests(self, info):
        return [{'name': individual.user.email, 'id': individual.id} for individual in self.join_requests.all()]

    def resolve_shopping_list(self, info):
        return self.groupshoppingitem_set.all()

    def resolve_meals(self, info):
        return self.groupmeal_set.all()
    
    

# Individual
class IndividualShoppingItemType(DjangoObjectType):
    """Shopping Item based on the IndividualShoppingItem"""
    class Meta:
        model = IndividualShoppingItem
        fields = ('id', 'name', 'quantity', 'unit')


class IndividualMealType(DjangoObjectType):
    """Meal based on the GroupShoppingItem"""
    class Meta:
        model = IndividualMeal
        fields = ('id', 'recipe', 'text', 'day', 'time')


class IndividualType(DjangoObjectType):
    """
    Individual that provides all information on the individual and the email/username for the corresponding user.
    Groups are resolved as a GroupType so that the individual member's shopping lists and meals can't be queried from the IndividualType
    """
    class Meta:
        model = Individual
        fields = ('id',)

    shopping_list = graphene.List(IndividualShoppingItemType)
    meals = graphene.List(IndividualMealType)
    groups = graphene.List(GroupType)
    requests = graphene.List(RequestType)
    email = graphene.String()
    username = graphene.String()

    def resolve_shopping_list(self, info):
        return self.individualshoppingitem_set.all()

    def resolve_meals(self, info):
        return self.individualmeal_set.all()

    def resolve_groups(self, info):
        return self.groups.all()

    def resolve_requests(self, info):
        return self.group_requests.all()

    def resolve_email(self, info):
        return self.user.email
    
    def resolve_username(self, info):
        return self.user.username

class LimitedIndividualType(graphene.ObjectType):
    """
    An individual type that only gives its id, groups, email and username.
    Used only in a superuser's query that gets all individuals. If recipe or
    meal information is needed, it can be accessed in the Django admin panel.
    """
    class Meta:
        model = Individual
        fields = ('id',)

    groups = graphene.List(GroupsType)
    email = graphene.String()
    username = graphene.String()

    def resolve_groups(self, info):
        return self.groups.all()

    def resolve_email(self, info):
        return self.user.email

    def resolve_username(self, info):
        return self.user.username

# *** Input Types ***
class IngredientInputType(graphene.InputObjectType):
    """Input type used to create an ingredient or shopping item"""
    name = graphene.String(required=True)
    quantity = graphene.String(required=True)
    unit = graphene.String(required=True)


# I'd like it to be a union of either 'Test Step 1' or {step: 'Test Step 1', order: 1}
# But it looks like a list in graphene can't contain union types
# Which makes it so if you want to do an unordered list, you're still going to have to
# specify 'step' even though it's fairly redundant - also makes things fairly obnoxious
# On the front end it will involve mapping step to { step: step }
class RecipeStepInputType(graphene.InputObjectType):
    """Input type to create a recipe prep step"""
    step = graphene.String(required=True)
    order = graphene.Int(required=False)

class Day(graphene.Enum):
    """Enum for the day of the week, values corresponding to what is expected by Django for the database"""
    MONDAY = "MON"
    TUESDAY = "TUE"
    WEDNESDAY = "WED"
    THURSDAY = "THU"
    FRIDAY = "FRI"
    SATURDAY = "SAT"
    SUNDAY = "SUN"


class Time(graphene.Enum):
    """Enum for the time of day for the meal, values corersponding to wjat is expected by Django for the database"""
    BREAKFAST = "B"
    LUNCH = "L"
    DINNER = "D"
    OTHER = "O"


class MealInputType(graphene.InputObjectType):
    """Input type used to create a meal"""
    text = graphene.String(required=False)
    recipeId = graphene.ID(required=False)
    day = Day(required=True)
    time = Time(required=True)
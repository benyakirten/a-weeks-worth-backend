from django.db import models
from django.contrib.auth.models import User
import uuid

# ********* BASE/ABSTRACT CLASSES *********


class BaseIngredient(models.Model):
    class Meta:
        abstract = True

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    quantity = models.CharField(max_length=100)
    unit = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.quantity} {self.unit} of {self.name}({self.id})"


class BaseMeal(models.Model):
    class Meta:
        abstract = True

    class DaysOfTheWeek(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"
        SUNDAY = "SUN", "Sunday"

    class MealTimes(models.TextChoices):
        BREAKFAST = "B", "Breakfast"
        LUNCH = "L", "Lunch"
        DINNER = "D", "Dinner"
        OTHER = "O", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipe = models.ForeignKey(
        'Recipe', blank=True, null=True, on_delete=models.SET_NULL)
    text = models.TextField(blank=True)
    day = models.CharField(
        max_length=3,
        choices=DaysOfTheWeek.choices
    )
    time = models.CharField(
        max_length=1,
        choices=MealTimes.choices
    )

    def __str__(self):
        return f"Meal: {self.text} for {self.day} at {self.time}({self.id})"

# ********* RECIPE *********


class RecipeIngredient(BaseIngredient):
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)


class RecipeStep(models.Model):
    step = models.TextField()
    order = models.IntegerField()
    recipe = models.ForeignKey('Recipe', on_delete=models.CASCADE)

    def __str__(self):
        return self.step


class Recipe(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    photo = models.CharField(max_length=254, blank=True)
    url = models.TextField(unique=True, blank=True)

    def __str__(self):
        return self.name

# ********* GROUP *********


class GroupShoppingItem(BaseIngredient):
    group = models.ForeignKey('Group', on_delete=models.CASCADE)


class GroupMeal(BaseMeal):
    group = models.ForeignKey('Group', on_delete=models.CASCADE)


class Group(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    members = models.ManyToManyField('Individual')
    join_requests = models.ManyToManyField('Individual', related_name="requests_received", blank=True)

    def __str__(self):
        return self.name


# ********* INDIVIDUAL *********
# To make things easier, instead of having a single user
# We have the authentication/JWT-based user, then we have the
# "Individual" which connects to the user automatically
# upon registration (c.f. apps.py and signals.py)
# And that contains the 'meaty' information we want
class IndividualShoppingItem(BaseIngredient):
    individual = models.ForeignKey('Individual', on_delete=models.CASCADE)


class IndividualMeal(BaseMeal):
    individual = models.ForeignKey('Individual', on_delete=models.CASCADE)


class Individual(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    groups = models.ManyToManyField('Group', blank=True)
    group_requests = models.ManyToManyField('Group', related_name="requests_made", blank=True)

    def __str__(self):
        return self.user.username

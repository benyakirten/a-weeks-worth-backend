from django.test import TestCase
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model

from .models import (
    RecipeIngredient,
    RecipeStep,
    Recipe,
    Individual
)

# Only recipe is tested because otherwise everything is just
# a Django model with default setup
class RecipeTest(TestCase):
    def setUp(self):
        super().setUp()
        Recipe.objects.create(name="Hamburger")

    def test_recipe_step_order(self):
        """
        Tests whether recipe prep is put in the order of the order field
        """
        ham = Recipe.objects.get(name="Hamburger")
        prep1 = RecipeStep.objects.create(step="Prep 2", order=2, recipe=ham)
        prep3 = RecipeStep.objects.create(step="Prep 4", order=4, recipe=ham)
        prep2 = RecipeStep.objects.create(step="Prep 3", order=3, recipe=ham)
        prep0 = RecipeStep.objects.create(step="Prep 1", order=1, recipe=ham)
        prep = ham.recipestep_set.all()
        self.assertEqual(prep[0], prep0)
        self.assertEqual(prep[1], prep1)
        self.assertEqual(prep[2], prep2)
        self.assertEqual(prep[3], prep3)
        
    def test_allow_multiple_blank_urls(self):
        """
        Tests that multiple recipes can have the same url if they are blank
        """
        ham = Recipe.objects.get(name="Hamburger")
        Recipe.objects.create(name="Lentil Soup")
        soup = Recipe.objects.get(name="Lentil Soup")
        self.assertIsNotNone(ham)
        self.assertIsNotNone(soup)

    def test_urls_unique_if_exist(self):
        """
        Tests that recipes cannot have the same url if they are not empty
        """
        test1 = Recipe.objects.create(name="Test Recipe1", url="https://www.google.com")
        with self.assertRaises(IntegrityError):
            test2 = Recipe.objects.create(name="Test Recipe2", url="https://www.google.com")

class UserTest(TestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="Test User", email="test@test.com", password="averytestpassword")
    
    def test_corresponding_individual(self):
        """
        Tests that an individual is created when a new user is instantiated
        """
        test_user = get_user_model().objects.get(email="test@test.com")

        individual = test_user.individual
        self.assertIsNotNone(individual)

    def test_individual_no_shopping_list(self):
        """
        Tests that the new individual has a blank shopping list
        """
        test_user = get_user_model().objects.get(email="test@test.com")
        shopping_list = test_user.individual.individualshoppingitem_set.all()
        self.assertEqual(len(shopping_list), 0)
    
    def test_individual_no_meals(self):
        """
        Tests that the new individual has a blank meal set
        """
        test_user = get_user_model().objects.get(email="test@test.com")
        meals = test_user.individual.individualmeal_set.all()
        self.assertEqual(len(meals), 0)
        
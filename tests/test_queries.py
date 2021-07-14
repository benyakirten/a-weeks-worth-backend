import json

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token
from django.contrib.auth import get_user_model

from aww.models import (
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

class QueriesTest(GraphQLTestCase):
    """
    This test suite tests the graphQL queries under schema.queries
    as well as most of the resolve methods of the types in schema.types
    """
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="Test User 1", email="queries1@test.com", password="thetestpassword")
        get_user_model().objects.create_user(username="Test User 2", email="queries2@test.com", password="thetestpassword")
        get_user_model().objects.create_superuser(username="Test Superuser 1", email="queriessuperuser@test.com", password="thetestpassword")
        
        self.user1 = get_user_model().objects.get(email="queries1@test.com")
        self.user2 = get_user_model().objects.get(email="queries2@test.com")
        self.superuser = get_user_model().objects.get(email="queriessuperuser@test.com")

        Recipe.objects.create(name="Test Recipe 1", url="https://www.google.com")
        Recipe.objects.create(name="Test Recipe 2", url="https://www.benyakiredits.com")

        self.recipe = Recipe.objects.get(name="Test Recipe 1")

        RecipeIngredient.objects.create(name="Test Name 1", unit="Test Unit 1", quantity="Test Quantity 1", recipe=self.recipe)
        RecipeIngredient.objects.create(name="Test Name 2", unit="Test Unit 2", quantity="Test Quantity 2", recipe=self.recipe)

        RecipeStep.objects.create(step="Test Step 1", order=1, recipe=self.recipe)
        RecipeStep.objects.create(step="Test Step 2", order=2, recipe=self.recipe)

        Group.objects.create(name="Test Group 1")

        self.group = Group.objects.get(name="Test Group 1")
        self.group.members.add(self.user1.individual)
        self.user1.individual.groups.add(self.group)

        GroupShoppingItem.objects.create(name="Test Name 1", unit="Test Unit 1", quantity="Test Quantity 1", group=self.group)
        GroupMeal.objects.create(text="Test Meal 1", day="MON", time="B", group=self.group)

        IndividualShoppingItem.objects.create(name="Test Name 1", unit="Test Unit 1", quantity="Test Quantity 1", individual=self.user1.individual)
        IndividualMeal.objects.create(text="Test Meal 1", day="MON", time="B", individual=self.user1.individual)

    def test_query_recipes(self):
        """
        Query recipes returns all recipes as RecipeType with their ids, names, photo, url, ingredients and steps
        """
        res = self.query('''
            query {
                recipes {
                    id
                    name
                    photo
                    ingredients {
                        name
                        quantity
                        unit
                    }
                    steps {
                        step
                        order
                    }
                }
            }
        ''')
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']

        recipe_ids = [str(recipe['id']) for recipe in data['recipes']]
        recipe_ids_expected = [str(recipe.id) for recipe in Recipe.objects.all()]

        self.assertListEqual(recipe_ids_expected, recipe_ids)

        recipes_expected = []
        for recipe in Recipe.objects.all():
            ings_raw = recipe.recipeingredient_set.all()
            ings_processed = [{'name': ing.name, 'quantity': ing.quantity, 'unit': ing.unit} for ing in ings_raw]
            steps_raw = recipe.recipestep_set.all()
            steps_processed = [{'step': step.step, 'order': step.order} for step in steps_raw]
            _recipe = {
                'id': str(recipe.id),
                'name': recipe.name,
                'photo': recipe.photo,
                'ingredients': ings_processed,
                'steps': steps_processed
            }
            recipes_expected.append(_recipe)
        self.assertListEqual(data['recipes'], recipes_expected)

    def test_query_recipe_urls(self):
        """Query recipeUrls returns all the urls on recipes as a list of strings"""
        res = self.query('''
            query {
                recipeUrls
            }
        ''')
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']
        urls = data['recipeUrls']

        self.assertIsInstance(urls, list)
        for url in urls:
            self.assertIsInstance(url, str)

        urls_expected = [recipe.url for recipe in Recipe.objects.all()]

        self.assertListEqual(urls, urls_expected)

    def test_query_groups(self):
        """
        Query groups returns all groups as GroupType with their ids, names and ingredient
        """
        res = self.query('''
            query {
                groups {
                    id
                    name
                    members
                }
            }
        ''')
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']

        group_ids = [group['id'] for group in data['groups']]
        group_ids_expected = [str(group.id) for group in Group.objects.all()]
        self.assertListEqual(group_ids_expected, group_ids)

        group_names = [group['name'] for group in data['groups']]
        group_names_expected = [group.name for group in Group.objects.all()]
        self.assertListEqual(group_names_expected, group_names)

        for group in data['groups']:
            self.assertIsInstance(group['members'], list)
            for item in group:
                self.assertIsInstance(item, str)
            

    def test_query_groups_no_requests(self):
        """
        Query groups doesn't have a requests field
        """
        res = self.query('''
            query {
                groups {
                    requests {
                        id
                        name
                    }
                }
            }
        ''')
        self.assertResponseHasErrors(res)
    
    def test_query_groups_no_meals(self):
        """
        Query groups doesn't have a meals field
        """
        res = self.query('''
            query {
                groups {
                    meals {
                        id
                    }
                }
            }
        ''')
        self.assertResponseHasErrors(res)

    def test_query_groups_no_shopping_list(self):
        """
        Query groups doesn't have a shoppingList field
        """
        res = self.query('''
            query {
                groups {
                    shoppingList {
                        name
                    }
                }
            }
        ''')
        self.assertResponseHasErrors(res)

    def test_query_individual_fails_without_superuser(self):
        """
        Query individual fails if the user is not a superuser
        """
        token = get_token(self.user1)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
            query individual($id: ID!)
                individual(id: $id) {
                    id
                }
            ''',
            op_name='individual',
            headers=headers
        )
        self.assertResponseHasErrors(res)

    def test_query_individual_succeeds_with_superuser(self):
        """
        Query individual succeeds if the user is a superuser
        Also the email field on UserType resolves to the corresponding user's email
        """
        token = get_token(self.superuser)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        userId = str(self.user1.individual.id)
        res = self.query(
            '''
                query individual($id: ID!) {
                    individual(id: $id) {
                        id
                        email
                        username
                        shoppingList {
                            name
                            quantity
                            unit
                        }
                        meals {
                            time
                            day
                            text
                        }
                        groups {
                            id
                            name
                        }
                    }
                }
            ''',
            op_name='individual',
            variables = {'id': userId},
            headers=headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']['individual']

        self.assertEqual(data['id'], userId)
        self.assertEqual(data['email'], self.user1.email)
        self.assertEqual(data['username'], self.user1.username)
        
        group_ids = [group['id'] for group in data['groups']]
        group_ids_expected = [str(group.id) for group in self.user1.individual.groups.all()]
        self.assertListEqual(group_ids, group_ids_expected)

        shopping_list_expected = [
            {
                'name': item.name,
                'quantity': item.quantity,
                'unit': item.unit
            } for item in self.user1.individual.individualshoppingitem_set.all()
        ]
        meals_expected = [
            {
                'time': meal.time,
                'day': meal.day,
                'text': meal.text
            } for meal in self.user1.individual.individualmeal_set.all()
        ]
        groups_expected = [
            {
                'id': str(group.id),
                'name': group.name,
            } for group in self.user1.individual.groups.all()
        ]

        self.assertListEqual(data['shoppingList'], shopping_list_expected)
        self.assertListEqual(data['meals'], meals_expected)
        self.assertListEqual(data['groups'], groups_expected)
    
    def test_query_all_individuals_fails_without_superuser(self):
        """
        Query all individuals fails if the user is not a superuser
        """
        token = get_token(self.user1)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query {
                        allIndividuals {
                            email
                        }
                    }
            ''',
            headers=headers
        )
        self.assertResponseHasErrors(res)

    def test_query_all_individuals_succeeds_with_superuser(self):
        """
        Query all individuals succeeds if the user is a superuser
        """
        token = get_token(self.superuser)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query {
                    allIndividuals {
                        email
                    }
                }
            ''',
            headers=headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']
        user_emails = [individual['email'] for individual in data['allIndividuals']]
        user_emails_expected = [user.email for user in get_user_model().objects.all()]
        self.assertListEqual(user_emails, user_emails_expected)
    
    def test_query_all_individuals_no_requests(self):
        """
        Query allIndividuals doesn't have a requests field
        """
        token = get_token(self.superuser)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query {
                    allIndividuals {
                        requests {
                            id
                            name
                        }
                    }
                }
            ''',
            headers=headers
        )
        self.assertResponseHasErrors(res)
    
    def test_query_all_individuals_no_meals(self):
        """
        Query allIndividuals doesn't have a meals field
        """
        token = get_token(self.superuser)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query {
                    allIndividuals {
                        meals {
                            id
                        }
                    }
                }
            ''',
            headers=headers
        )
        self.assertResponseHasErrors(res)

    def test_query_all_individuals_no_shopping_list(self):
        """
        Query allIndividuals doesn't have a shoppingList field
        """
        token = get_token(self.superuser)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query {
                    allIndividuals {
                        shoppingList {
                            name
                        }
                    }
                }
            ''',
            headers=headers
        )
        self.assertResponseHasErrors(res)

    def test_query_group_fails_if_user_not_in_group(self):
        """
        Query group fails if the user is not in the group
        """
        token = get_token(self.user2)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query group($id: ID!)
                    group(id: $id) {
                        id
                    }
                }
            ''',
            op_name='group',
            variables={'id': str(self.group.id)},
            headers=headers
        )
        self.assertResponseHasErrors(res)

    def test_query_group_succeeds_if_user_in_group(self):
        """
        Query group succeeds if the user is in the group
        """
        token = get_token(self.user1)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        group_id = str(self.group.id)
        res = self.query(
            '''
                query group($id: ID!) {
                    group(id: $id) {
                        id
                        name
                        members
                        shoppingList {
                            name
                            quantity
                            unit
                        }
                        meals {
                            day
                            time
                            text
                        }
                    }
                }
            ''',
            op_name='group',
            variables={'id': group_id},
            headers=headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']['group']
        self.assertEqual(data['id'], group_id)

        shopping_list_expected = [
            {
                'name': item.name,
                'quantity': item.quantity,
                'unit': item.unit
            } for item in self.group.groupshoppingitem_set.all()
        ]
        meals_expected = [
            {
                'day': meal.day,
                'time': meal.time,
                'text': meal.text
            } for meal in self.group.groupmeal_set.all()
        ]
        members_expected = [member.user.email for member in self.group.members.all()]
        
        self.assertListEqual(data['shoppingList'], shopping_list_expected)
        self.assertListEqual(data['meals'], meals_expected)
        self.assertListEqual(data['members'], members_expected)
    
    def test_my_groups(self):
        """
        Query myGroups returns the groups that the user is a member in
        """
        token = get_token(self.user1)
        headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        res = self.query(
            '''
                query {
                    myGroups {
                        id
                    }
                }
            ''',
            headers=headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']
        group_ids = [group['id'] for group in data['myGroups']]

        groups = Group.objects.all()
        group_ids_expected = [str(group.id) for group in groups if self.user1.individual in group.members.all()]

        self.assertListEqual(group_ids, group_ids_expected)
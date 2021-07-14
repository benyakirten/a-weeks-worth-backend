import json

from django.contrib.auth import get_user_model

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token

from aww.models import Recipe

class RecipeMutationTest(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="Test User", email="recipemutation@test.com", password="testpassword")
        self.user = get_user_model().objects.get(email="recipemutation@test.com")
        self.token = get_token(self.user)
        self.headers = {"HTTP_AUTHORIZATION": f"JWT {self.token}"}

        Recipe.objects.create(name="Totally cool test recipe")
        self.recipe = Recipe.objects.get(name="Totally cool test recipe")
    
    def test_create_recipe_not_works_without_authentication(self):
        res = self.query(
            '''
                    mutation createRecipe($name: String!) {
                        createRecipe(name: $name) {
                            recipe {
                                id
                                name
                            }
                        }
                    }
            ''',
            op_name='createRecipe',
            variables={'name':'Some new recipe'}
        )
        self.assertResponseHasErrors(res)

    def test_update_recipe_not_works_without_authentication(self):
        res = self.query(
            '''
                mutation updateRecipe($id: ID!, $name: String!) {
                    updateRecipe(id: $id, name: $name) {
                        recipe {
                            id
                            name
                        }
                    }
                }
            ''',
            op_name='updateRecipe',
            variables={'id': str(self.recipe.id), 'name':'A different title'}
        )
        self.assertResponseHasErrors(res)

    def test_delete_recipe_not_works_without_authentication(self):
        res = self.query(
            '''
                    mutation deleteRecipe($id: ID!) {
                        deleteRecipe(id: $id) {
                            recipe {
                                id
                                name
                            }
                        }
                    }
            ''',
            op_name='deleteRecipe',
            variables={'id': str(self.recipe.id)}
        )
        self.assertResponseHasErrors(res)

    def test_complete_process(self):
        res_create = self.query(
            '''
                mutation createRecipe($name: String!) {
                    createRecipe(name: $name) {
                        recipe {
                            id
                            name
                        }
                    }
                }
            ''',
            op_name='createRecipe',
            variables={'name':'Some new recipe'},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_create)

        new_recipe = json.loads(res_create.content)['data']['createRecipe']['recipe']
        recipe_object = Recipe.objects.get(name='Some new recipe')

        self.assertEqual(new_recipe['id'], str(recipe_object.id))
        self.assertEqual(new_recipe['name'], recipe_object.name)

        res_update = self.query(
            '''
                mutation updateRecipe($id: ID!, $name: String!, $photo: String!, $ingredients: [IngredientInputType!], $steps: [RecipeStepInputType!]) {
                    updateRecipe(id: $id, name: $name, photo: $photo, ingredients: $ingredients, steps: $steps) {
                        recipe {
                            name
                            id
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
                }
            ''',
            op_name='updateRecipe',
            variables={
                'id': new_recipe['id'],
                'name': 'A different title',
                'photo': "https://www.google.com",
                'ingredients': [
                    {
                        'name': 'Test Ingredient 1',
                        'quantity': 'Test Quantity 1',
                        'unit': 'Test Unit 1'
                    }
                ],
                'steps': [
                    {
                        'step': 'Test Step 1',
                        'order': 1
                    }
                ]
            },
            headers=self.headers
        )
        self.assertResponseNoErrors(res_update)

        update_recipe = json.loads(res_update.content)['data']['updateRecipe']['recipe']
        recipe_object_updated = Recipe.objects.get(id=recipe_object.id)

        self.assertEqual(recipe_object.id, recipe_object_updated.id)
        self.assertEqual(update_recipe['id'], str(recipe_object_updated.id))
        self.assertEqual(update_recipe['name'], recipe_object_updated.name)

        recipe_ingredients_formatted = [
            {'name': ing.name, 'quantity': ing.quantity, 'unit': ing.unit}
            for ing in recipe_object.recipeingredient_set.all()
        ]
        recipe_steps_formatted = [
            {'step': step.step, 'order': step.order}
            for step in recipe_object.recipestep_set.all()
        ]
        self.assertListEqual(update_recipe['ingredients'], recipe_ingredients_formatted)
        self.assertListEqual(update_recipe['steps'], recipe_steps_formatted)

        res_delete = self.query(
            '''
                mutation deleteRecipe($id: ID!) {
                    deleteRecipe(id: $id) {
                        recipe {
                            name
                            id
                        }
                    }
                }
            ''',
            op_name='deleteRecipe',
            variables={'id': new_recipe['id']},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_delete)
        delete_recipe = json.loads(res_delete.content)['data']['deleteRecipe']['recipe']

        self.assertEqual(delete_recipe['id'], str(recipe_object_updated.id))
        self.assertEqual(delete_recipe['name'], recipe_object_updated.name)

        with self.assertRaises(Recipe.DoesNotExist):
            Recipe.objects.get(name=recipe_object_updated.name)
        with self.assertRaises(Recipe.DoesNotExist):
            Recipe.objects.get(name=recipe_object.name)
        with self.assertRaises(Recipe.DoesNotExist):
            Recipe.objects.get(name=recipe_object.id)
import json

from django.contrib.auth import get_user_model

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token

from aww.models import Group

class GroupMutationTest(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="Test User", email="groupmutation@test.com", password="testpassword")
        self.user = get_user_model().objects.get(email="groupmutation@test.com")
        self.token = get_token(self.user)
        self.headers = {"HTTP_AUTHORIZATION": f"JWT {self.token}"}

        Group.objects.create(name="Test Group For Mutations")
        self.group = Group.objects.get(name="Test Group For Mutations")
    
    def test_create_group_not_works_without_authentication(self):
        res = self.query(
            '''
                    mutation createGroup($name: String!) {
                        createGroup(name: $name) {
                            group {
                                id
                                name
                            }
                        }
                    }
            ''',
            op_name='createGroup',
            variables={'name':'Some new group, please'}
        )
        self.assertResponseHasErrors(res)

    def test_update_group_not_works_without_authentication(self):
        res = self.query(
            '''
                mutation updateGroup($id: ID!, $name: String!, $shoppingList: [IngredientInputType!]) {
                    updateGroup(id: $id, name: $name, shoppingList: $shoppingList) {
                        group {
                            id
                            name
                            shoppingList {
                                name
                                quantity
                                unit
                            }
                        }
                    }
                }
            ''',
            op_name='updateGroup',
            variables={
                'id': str(self.group.id),
                'name':'A different name for this mutation group',
                'shoppingList': [
                    {
                        'name': 'Test Ingredient 1',
                        'quantity': 'Test Quantity 1',
                        'unit': 'Test Unit 1'
                    }
                ]
            }
        )
        self.assertResponseHasErrors(res)

    def test_delete_group_not_works_without_authentication(self):
        res = self.query(
            '''
                    mutation deleteGroup($id: ID!) {
                        deleteGroup(id: $id) {
                            group {
                                id
                                name
                            }
                        }
                    }
            ''',
            op_name='deleteGroup',
            variables={'id': str(self.group.id)}
        )
        self.assertResponseHasErrors(res)

    def test_complete_process(self):
        res_create = self.query(
            '''
                mutation createGroup($name: String!) {
                    createGroup(name: $name) {
                        group {
                            id
                            name
                        }
                    }
                }
            ''',
            op_name='createGroup',
            variables={'name':'Some new group for the group mutation tests'},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_create)

        new_group = json.loads(res_create.content)['data']['createGroup']['group']
        group_object = Group.objects.get(id=new_group['id'])

        self.assertEqual(new_group['id'], str(group_object.id))
        self.assertEqual(new_group['name'], group_object.name)

        res_update = self.query(
            '''
                mutation updateGroup($id: ID!, $name: String!, $shoppingList: [IngredientInputType!]) {
                    updateGroup(id: $id, name: $name, shoppingList: $shoppingList) {
                        group {
                            name
                            id
                            shoppingList {
                                name
                                quantity
                                unit
                            }
                        }
                    }
                }
            ''',
            op_name='updateGroup',
            variables={
                'id': new_group['id'],
                'name': 'A different title for the group mutation tests group',
                'ingredients': [
                    {
                        'name': 'Test Ingredient 1',
                        'quantity': 'Test Quantity 1',
                        'unit': 'Test Unit 1'
                    }
                ],
            },
            headers=self.headers
        )
        self.assertResponseNoErrors(res_update)

        update_group = json.loads(res_update.content)['data']['updateGroup']['group']
        group_object_updated = Group.objects.get(id=group_object.id)

        self.assertEqual(group_object.id, group_object_updated.id)
        self.assertEqual(update_group['id'], str(group_object_updated.id))
        self.assertEqual(update_group['name'], group_object_updated.name)

        group_shopping_list_formatted = [
            {'name': item.name, 'quantity': item.quantity, 'unit': item.unit}
            for item in group_object.groupshoppingitem_set.all()
        ]
        self.assertListEqual(update_group['shoppingList'], group_shopping_list_formatted)

        res_delete = self.query(
            '''
                mutation deleteGroup($id: ID!) {
                    deleteGroup(id: $id) {
                        group {
                            name
                            id
                        }
                    }
                }
            ''',
            op_name='deleteGroup',
            variables={'id': new_group['id']},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_delete)
        delete_group = json.loads(res_delete.content)['data']['deleteGroup']['group']

        self.assertEqual(delete_group['id'], str(group_object_updated.id))
        self.assertEqual(delete_group['name'], group_object_updated.name)

        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(name=group_object_updated.name)
        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(name=group_object.name)
        with self.assertRaises(Group.DoesNotExist):
            Group.objects.get(name=group_object.id)
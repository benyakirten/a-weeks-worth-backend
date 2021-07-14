import json

from django.contrib.auth import get_user_model

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token

from aww.models import Individual, Group

class RecipeMutationTest(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="Test User", email="individualmutation@test.com", password="testpassword")
        get_user_model().objects.create_user(username="Test User 2", email="individualmutation2@test.com", password="testpassword")
        self.user = get_user_model().objects.get(email="individualmutation@test.com")
        self.user2 = get_user_model().objects.get(email="individualmutation2@test.com")
        self.token = get_token(self.user)
        self.token2 = get_token(self.user2)
        self.headers = {"HTTP_AUTHORIZATION": f"JWT {self.token}"}
        self.headers2 = {"HTTP_AUTHORIZATION": f"JWT {self.token2}"}
        self.individual = self.user.individual
        self.individual2 = self.user2.individual

        Group.objects.create(name="Test Group")
        self.group = Group.objects.get(name="Test Group")
        self.group.members.add(self.individual2)
    
    def test_update_individual_not_works_without_authentication(self):
        """
        Tests updateIndividual mutation to see if it works if the user is not authenticated
        """
        res = self.query(
            '''
                mutation updateIndividual($id: ID!, $shoppingList: [IngredientInputType!]) {
                    updateIndividual(id: $id, shoppingList: $shoppingList) {
                        individual {
                            id
                            shoppingList
                        }
                    }
                }
            ''',
            op_name='updateIndividual',
            variables={
                'id': str(self.individual.id),
                'ingredients': [
                    {
                        'name': 'Test Ingredient 1',
                        'quantity': 'Test Quantity 1',
                        'unit': 'Test Unit 1'
                    }
                ]
                # Meals cannot be tested because they require enum values for day/time
                # And enums can't be JSON serialized
            }
        )
        self.assertResponseHasErrors(res)
    
    def test_update_individual_not_works_without_authentication(self):
        """
        Tests updateIndividual mutation with normal parameters
        """
        res = self.query(
            '''
                mutation updateIndividual($id: ID!, $shoppingList: [IngredientInputType!]) {
                    updateIndividual(id: $id, shoppingList: $shoppingList) {
                        individual {
                            id
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
                        }
                    }
                }
            ''',
            op_name='updateIndividual',
            variables={
                'id': str(self.individual.id),
                'shoppingList': [
                    {
                        'name': 'Test Ingredient 1',
                        'quantity': 'Test Quantity 1',
                        'unit': 'Test Unit 1'
                    }
                ]
            },
            headers=self.headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']['updateIndividual']['individual']

        expected_shopping_list = [
            {'name': item.name, 'quantity': item.quantity, 'unit': item.unit}
            for item in self.individual.individualshoppingitem_set.all()
        ]
        expected_meals = [
            {'time': meal.time, 'day': meal.day, 'text': meal.text}
            for meal in self.individual.individualmeal_set.all()
        ]
        self.assertListEqual(data['shoppingList'], expected_shopping_list)
        self.assertListEqual(data['meals'], expected_meals)

    def test_request_access_not_works_without_authentication(self):
        """
        Tests requestAccess mutation to see if it works if the user is not authenticated
        """
        res = self.query(
            '''
                mutation requestAccess($id: ID!) {
                    requestAccess(id: $id) {
                        group {
                            id
                            members
                        }
                    }
                }
            ''',
            op_name='requestAccess',
            variables={'id': str(self.group.id)}
        )
        self.assertResponseHasErrors(res)

    def test_cancel_request_not_works_without_authentication(self):
        """
        Tests requestAccess mutation to see if it works if the user is not authenticated
        """
        self.group.join_requests.add(self.individual)
        self.individual.group_requests.add(self.group)
        # There needs to be a request to attempt to cancel, otherwise
        # this test would fail because there isn't. It needs to fail because
        # there's no headers, not because of any other reason
        res = self.query(
            '''
                    mutation cancelRequest($id: ID!, $name: String!) {
                        cancelRequest(id: $id, name: $name) {
                            success
                        }
                    }
            ''',
            op_name='cancelRequest',
            variables={'id': str(self.group.id)}
        )
        self.assertResponseHasErrors(res)

        self.group.join_requests.remove(self.individual)
        self.individual.group_requests.remove(self.group)

    def test_invite_to_group_not_works_without_authentication(self):
        res = self.query(
            '''
                mutation inviteToGroup($invitedId: ID!, $groupId: ID!) {
                    inviteToGroup(invitedId: $invitedId, groupId: $groupID) {
                        individual {
                            id
                            email
                        }
                        group {
                            id
                            name
                        }
                    }
                }
            ''',
            op_name='inviteToGroup',
            variables={'invitedId': str(self.individual.id), 'groupId': str(self.group.id)}
        )
        self.assertResponseHasErrors(res)
    
    def test_invite_to_group_not_works_not_in_group(self):
        res = self.query(
            '''
                mutation inviteToGroup($invitedId: ID!, $groupId: ID!) {
                    inviteToGroup(invitedId: $invitedId, groupId: $groupID) {
                        individual {
                            id
                            email
                        }
                        group {
                            id
                            name
                        }
                    }
                }
            ''',
            op_name='inviteToGroup',
            variables={'invitedId': str(self.individual.id), 'groupId': str(self.group.id)},
            # self.headers is for self.individual, which is not in the group
            headers=self.headers
        )
        self.assertResponseHasErrors(res)
    
    def test_leave_group_not_works_without_authentication(self):
        """
        Tests leave group mutation to see if it works without the proper authentication
        """
        self.group.members.add(self.individual)
        self.individual.groups.add(self.group)
        res = self.query(
            '''
                mutation leaveGroup($id: ID!) {
                    leaveGroup(id: $id) {
                        individual {
                            id
                            groups {
                                id
                                name
                            }
                        }
                    }
                }
            ''',
            op_name='leaveGroup',
            variables={'id': str(self.group.id)}
        )
        self.assertResponseHasErrors(res)

        self.group.members.remove(self.individual)
        self.individual.groups.remove(self.group)

    def test_leave_group_not_works_not_in_group(self):
        """
        Tests leave group mutation to see if it fails if user's individual is not in the group
        """
        res = self.query(
            '''
                mutation leaveGroup($id: ID!) {
                    leaveGroup(id: $id) {
                        individual {
                            id
                            groups {
                                id
                                name
                            }
                        }
                    }
                }
            ''',
            op_name='leaveGroup',
            variables={'id': str(self.group.id)},
            # self.headers is for self.individual, who is not in the group
            headers=self.headers
        )
        self.assertResponseHasErrors(res)

    def test_complete_process(self):
        """
        Tests the following process:
        1. User requests access to group
        2. User cancels request
        3. User requests access again
        4. User 2 accepts request
        5. User leaves group
        """
        res_req_1 = self.query(
            '''
                mutation requestAccess($id: ID!) {
                    requestAccess(id: $id) {
                        individual {
                            id
                        }
                    }
                }
            ''',
            op_name='requestAccess',
            variables={'id': str(self.group.id)},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_req_1)
        self.assertIn(self.group, self.individual.group_requests.all())
        self.assertIn(self.individual, self.group.join_requests.all())
        
        res_cancel = self.query(
            '''
                    mutation cancelRequest($id: ID!) {
                        cancelRequest(id: $id) {
                            success
                        }
                    }
            ''',
            op_name='cancelRequest',
            variables={'id': str(self.group.id)},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_cancel)
        data_cancel = json.loads(res_cancel.content)['data']['cancelRequest']

        self.assertTrue(data_cancel['success'])
        self.assertNotIn(self.group, self.individual.group_requests.all())
        self.assertNotIn(self.individual, self.group.join_requests.all())

        res_req_2 = self.query(
            '''
                mutation requestAccess($id: ID!) {
                    requestAccess(id: $id) {
                        individual {
                            id
                        }
                    }
                }
            ''',
            op_name='requestAccess',
            variables={'id': str(self.group.id)},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_req_2)
        self.assertIn(self.group, self.individual.group_requests.all())
        self.assertIn(self.individual, self.group.join_requests.all())

        res_accept = self.query(
            '''
                mutation inviteToGroup($invitedId: ID!, $groupId: ID!) {
                    inviteToGroup(invitedId: $invitedId, groupId: $groupId) {
                        individual {
                            id
                        }
                        group {
                            id
                            name
                            members
                        }
                    }
                }
            ''',
            op_name='inviteToGroup',
            variables={'invitedId': str(self.individual.id), 'groupId': str(self.group.id)},
            # self.headers2 is for individual2, who is in the group
            headers=self.headers2
        )
        self.assertResponseNoErrors(res_accept)

        self.assertIn(self.individual, self.group.members.all())
        self.assertIn(self.group, self.individual.groups.all())

        self.assertNotIn(self.individual, self.group.join_requests.all())
        self.assertNotIn(self.group, self.individual.group_requests.all())

        res_leave = self.query(
            '''
                mutation leaveGroup($id: ID!) {
                    leaveGroup(id: $id) {
                        individual {
                            id
                            groups {
                                id
                                name
                            }
                        }
                    }
                }
            ''',
            op_name='leaveGroup',
            variables={'id': str(self.group.id)},
            headers=self.headers
        )
        self.assertResponseNoErrors(res_leave)
        self.assertNotIn(self.individual, self.group.members.all())
        self.assertNotIn(self.group, self.individual.groups.all())

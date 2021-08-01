import json

from django.contrib.auth import get_user_model

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token

class UserMutationTest(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create(username="TestUser", email="usermutation@test.com", password="testpassword", first_name="identifier")
        user = get_user_model().objects.get(first_name="identifier")
        token = get_token(user)
        self.headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}

    def test_update_details_not_work_without_authentication(self):
        """
        Tests whether the update details mutation raises an error if the user isn'tauthenticated
        """
        res = self.query(
            """
                mutation updateDetails($email: String, $username: String) {
                    updateDetails(email: $email, username: $username) {
                        user {
                            username
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "email": "coolerusermutation@test.com",
                "username": "CoolerTestUser"
            }
        )
        self.assertResponseHasErrors(res)
    
    def test_update_details_not_work_if_neither_item_provided(self):
        """
        Tests whether the update details mutation raises an error if neither a new email nor username is provided
        """
        res = self.query(
            """
                mutation updateDetails($email: String, $username: String) {
                    updateDetails(email: $email, username: $username) {
                        user {
                            username
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            headers=self.headers
        )
        self.assertResponseHasErrors(res)

    def test_update_details_fails_with_invalid_email(self):
        """
        Tests whether the update details mutation raises an error if the provided email isn't RC5322-compliant
        """
        res = self.query(
            """
                mutation updateDetails($email: String) {
                    updateDetails(email: $email) {
                        user {
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "email": "noampersand"
            },
            headers=self.headers
        )
        self.assertResponseHasErrors(res)

        res2 = self.query(
            """
                mutation updateDetails($email: String) {
                    updateDetails(email: $email) {
                        user {
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "email": "@example.com"
            },
            headers=self.headers
        )
        self.assertResponseHasErrors(res2)

    def test_update_details_fails_if_email_already_exists(self):
        """
        Tests whether the update details mutation fails if another user is using the email
        the user is attempting to update their account to
        """
        get_user_model().objects.create(username="TestUser2", email="usermutation2@test.com", password="testpassword")
        res = self.query(
            """
                mutation updateDetails($email: String) {
                    updateDetails(email: $email) {
                        user {
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={ "email": "usermutation2@test.com" },
            headers=self.headers
        )
        self.assertResponseHasErrors(res)

    def test_update_details_fails_if_username_already_exists(self):
        """
        Tests whether the update details mutation fails if another user is using the username
        the user is attempting to update their account to
        """
        get_user_model().objects.create(username="TestUser2", email="usermutation2@test.com", password="testpassword")
        res = self.query(
            """
                mutation updateDetails($username: String) {
                    updateDetails(username: $username) {
                        user {
                            username
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={ "username": "TestUser2" },
            headers=self.headers
        )
        self.assertResponseHasErrors(res)
    
    def test_update_details_fails_with_invalid_username(self):
        """
        Tests whether the update details mutation raises an error if the provided uw34nqm3 is longer than 150 characters or contains invalid characters
        """
        res = self.query(
            """
                mutation updateDetails($username: String) {
                    updateDetails(username: $username) {
                        user {
                            username
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "username": "  cooldudeè  "
            },
            headers=self.headers
        )
        self.assertResponseHasErrors(res)

        res2 = self.query(
            """
                mutation updateDetails($username: String) {
                    updateDetails(username: $username) {
                        user {
                            username
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "username": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaab"
            },
            headers=self.headers
        )
        self.assertResponseHasErrors(res2)

    def test_update_details_works_with_authentication_and_either_input(self):
        """
        Tests whether the update details mutation works if only one of the two details is provided
        """
        res = self.query(
            """
                mutation updateDetails($email: String) {
                    updateDetails(email: $email) {
                        user {
                            username
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "email": "cooltestname@test.com"
            },
            headers=self.headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']['updateDetails']['user']
        updated_user = get_user_model().objects.get(first_name="identifier")
        self.assertEqual(updated_user.email, data['email'])

        res2 = self.query(
            """
                mutation updateDetails($username: String) {
                    updateDetails(username: $username) {
                        user {
                            username
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "username": "Cooltestname"
            },
            headers=self.headers
        )
        self.assertResponseNoErrors(res2)
        data2 = json.loads(res2.content)['data']['updateDetails']['user']
        updated_user2 = get_user_model().objects.get(first_name="identifier")
        self.assertEqual(updated_user2.username, data2['username'])
    
    def test_update_details_works_with_both_inputs(self):
        """
        Tests whether the update details mutation works if both details are provided
        """
        res = self.query(
            """
                mutation updateDetails($email: String, $username: String) {
                    updateDetails(email: $email, username: $username) {
                        user {
                            username
                            email
                        }
                    }
                }
            """,
            op_name="updateDetails",
            variables={
                "email": "coolertestname@test.com",
                "username": "coolertestuser"
            },
            headers=self.headers
        )
        self.assertResponseNoErrors(res)
        data = json.loads(res.content)['data']['updateDetails']['user']
        user = get_user_model().objects.get(first_name="identifier")
        self.assertEqual(user.email, data['email'])
        self.assertEqual(user.username, data['username'])
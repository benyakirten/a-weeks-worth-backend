import json

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings

from graphene_django.utils.testing import GraphQLTestCase
from graphql_jwt.shortcuts import get_token

# Django does this by default when running testing, but it never hurts to be safe
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class MessageMeTest(GraphQLTestCase):
    def setUp(self):
        super().setUp()
        get_user_model().objects.create_user(username="Coolest user ever", email="coolio@cool.com", password="sosweetbro")
        self.user = get_user_model().objects.get(email="coolio@cool.com")
        token = get_token(self.user)
        self.headers = {"HTTP_AUTHORIZATION": f"JWT {token}"}
        self.message = 'You are the coolest person ever'

    def test_send_email(self):
        res = self.query(
            '''
                mutation messageMe($message: String!) {
                    messageMe(message: $message) {
                        success
                    }
                }
            ''',
            op_name='messageMe',
            variables={'message': self.message},
            headers=self.headers
        )
        self.assertResponseNoErrors(res)
        success = json.loads(res.content)['data']['messageMe']['success']
        self.assertTrue(success)

        self.assertEquals(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(self.message, email.body)


        
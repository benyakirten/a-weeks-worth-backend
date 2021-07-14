import re
import json

from django.core import mail
from django.test import override_settings

from graphene_django.utils.testing import GraphQLTestCase

# Django does this by default when running testing, but it never hurts to be safe
@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class ActivateEmailTest(GraphQLTestCase):
    """
    This test will create a user, intercept the email that's sent out, find the activation code
    and activate the user
    """
    def setUp(self):
        super().setUp()
        self.emailRegExPat = r'A Week\'s Worth:(.*)'

    
    def test_whole_process(self):
        res_register = self.query(
            '''
                mutation register($email: String!, $username: String!, $password1: String!, $password2: String!) {
                    register(email: $email, username: $username, password1: $password1, password2: $password2) {
                        success
                        token
                    }
                }
            ''',
            op_name='register',
            variables={
                'email': 'wholetest1@test.com',
                'username': 'sirtestingtonthethird',
                'password1': 'myd1gn1f13dp4ssw0rd',
                'password2': 'myd1gn1f13dp4ssw0rd'
            }
        )

        self.assertResponseNoErrors(res_register)
        register_success = json.loads(res_register.content)['data']['register']['success']
        self.assertTrue(register_success)

        email_body = mail.outbox[0].body
        match = re.search(self.emailRegExPat, email_body)
        activation_token = match.groups()[0].strip()

        res_verify_account = self.query(
            '''
                mutation verifyAccount($token: String!) {
                    verifyAccount(token: $token) {
                        success
                        errors
                    }
                }
            ''',
            op_name='verifyAccount',
            variables={
                'token': activation_token
            }
        )

        self.assertResponseNoErrors(res_verify_account)
        verify_account_success = json.loads(res_verify_account.content)['data']['verifyAccount']['success']
        self.assertTrue(verify_account_success)
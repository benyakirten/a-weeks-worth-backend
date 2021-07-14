import os

import graphene
from graphql_jwt.decorators import login_required
from django.core.mail import send_mail

class MessageMe(graphene.Mutation):
    class Arguments:
        message = graphene.String(required = True)

    success = graphene.Field(graphene.Boolean)

    @classmethod
    @login_required
    def mutate(cls, root, info, message):
        # print(os.environ.get('SENDGRID_EMAIL_FROM'))
        # print(os.environ.get('MY_EMAIL_ADDRESS'))
        emails_sent = send_mail(
            f'{info.context.user.email} has sent you a message from A Week\'s Worth',
            message,
            os.environ.get('SENDGRID_EMAIL_FROM'),
            [os.environ.get('MY_EMAIL_ADDRESS')],
            fail_silently=False
        )
        return MessageMe(success=emails_sent == 1)

class Mutation(graphene.ObjectType):
    message_me = MessageMe.Field()
import re

from django.contrib.auth import get_user_model

import graphene
from graphql_jwt.decorators import login_required
from graphql_auth.schema import UserNode

class UpdateDetails(graphene.Mutation):
    """Allows the user to change their email and/or username"""
    class Arguments:
        email = graphene.String(required=False)
        username = graphene.String(required=False)

    user = graphene.Field(UserNode)

    @classmethod
    @login_required
    def mutate(cls, root, info, email="", username=""):
        if not email and not username:
            raise Exception("Either or both a new email and/or username must be provided")
        user = info.context.user
        error = None
        if email:
            if not re.search(r"""(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])""", email):
                raise Exception("Email address invalid")
            try:
                user_already_with_email = get_user_model().objects.get(email=email)
                if user.email != user_already_with_email.email:
                    # If this is false It's the user's email with no change -- no reason to save it
                    # If it's true -- we got a problem
                    # The problem will be caught if we raise it here, so we will raise it in a second
                    error = "Email address already in use"
            except:
                user.email = email
                user.save(update_fields=['email'])
        
        if error:
            raise Exception(error)
            
        if username:
            if not re.search(r'^[\w\.@+-]+$', username) or len(username) > 150:
                raise Exception("Username must be 150 characters or fewer, consisting only of letters, digits and @/./+/-/_ only.")
            try:
                user_already_with_username = get_user_model().objects.get(username=username)
                if user.username != user_already_with_username.username:
                    # If this is false It's the user's username with no change -- no reason to save it
                    # If it's true -- we got a problem
                    # Again, the error can't be raised here, or it'll be caught
                    # So we have to do it afterwards
                    error = "Username already in use"
            except:
                user.username = username
                user.save(update_fields=['username'])
        
        if error:
            raise Exception(error)

        return UpdateDetails(user=user)

class Mutation(graphene.ObjectType):
    update_details = UpdateDetails.Field()
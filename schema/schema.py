import graphene
from graphql_auth import mutations
from graphql_auth.schema import UserQuery, MeQuery

from .queries import Query as OtherQuery
from .mutations.individual_mutation import Mutation as IndividualMutation
from .mutations.recipe_mutation import Mutation as RecipeMutation
from .mutations.group_mutation import Mutation as GroupMutation
from .mutations.other_mutation import Mutation as OtherMutation

class Query(UserQuery, MeQuery, OtherQuery, graphene.ObjectType):
    pass

class AuthMutation(graphene.ObjectType):
    register = mutations.Register.Field()
    verify_account = mutations.VerifyAccount.Field()
    update_account = mutations.UpdateAccount.Field()
    delete_account = mutations.DeleteAccount.Field()
    token_auth = mutations.ObtainJSONWebToken.Field()
    resend_activation_email = mutations.ResendActivationEmail.Field()
    send_password_reset_email = mutations.SendPasswordResetEmail.Field()
    password_reset = mutations.PasswordReset.Field()
    password_change = mutations.PasswordChange.Field()

class Mutation(
        AuthMutation,
        OtherMutation,
        GroupMutation,
        IndividualMutation,
        RecipeMutation,
        graphene.ObjectType
    ):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
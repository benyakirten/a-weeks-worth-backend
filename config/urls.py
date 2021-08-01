# a week's worth URL Configuration
from django.contrib import admin
from django.urls import path, include
from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from graphene_django.views import GraphQLView

urlpatterns = [
    path('admin/', admin.site.urls),
    url('graphql/', csrf_exempt(GraphQLView.as_view(graphiql=True)))
]

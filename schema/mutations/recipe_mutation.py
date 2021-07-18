import copy

import graphene
from graphql_jwt.decorators import login_required

from aww.models import (
    RecipeIngredient,
    RecipeStep,
    Recipe
)

from ..types import (
    GroupType,
    IndividualType,
    RecipeType,
    IngredientInputType,
    RecipeStepInputType,
    MealInputType
)

class CreateRecipe(graphene.Mutation):
    """Create a recipe with a unique name and optionally photo, ingredients and steps."""
    class Arguments:
        name = graphene.String(required=True)
        photo = graphene.String(required=False)
        # URL can only be set on creation, never updated
        url = graphene.String(required=False)
        ingredients = graphene.List(IngredientInputType, required=False)
        steps = graphene.List(RecipeStepInputType, required=False)

    recipe = graphene.Field(RecipeType)

    @classmethod
    @login_required
    def mutate(cls, root, info, name, photo="", url="", ingredients=[], steps = []):
        if len(ingredients) > 150:
            raise Exception("A recipe may only have 150 ingredients")
        if len(steps) > 200:
            raise Exception("A recipe may only have 200 steps")

        recipe = Recipe(name=name)
        if photo:
            recipe.photo = photo
        if url:
            # If the URL isn't unique, an error will be raised by Django
            recipe.url = url
        recipe.save()

        if ingredients:
            for i in ingredients:
                recipe.recipeingredient_set.create(
                    name=i.name,
                    quantity=i.quantity,
                    unit=i.unit
                )
        if steps:
            for step in steps:
                if step.order:
                    recipe.recipestep_set.create(
                        step=step.step,
                        order=step.order
                    )
                else:
                    recipe.recipeste_set.create(
                        step=step.step
                    )
        return CreateRecipe(recipe=recipe)


class UpdateRecipe(graphene.Mutation):
    """
    Update a recipe with a new name/photo/ingredients/steps.
    This mutation will delete all current ingredients and steps if either of those values are provided.
    """
    class Arguments:
        id = graphene.ID()
        name = graphene.String(required=False)
        photo = graphene.String(required=False)
        ingredients = graphene.List(IngredientInputType, required=False)
        steps = graphene.List(RecipeStepInputType, required=False)

    recipe = graphene.Field(RecipeType)

    @classmethod
    @login_required
    def mutate(cls, root, info, id, name="", photo="", ingredients=[], steps=[]):
        # We have to update by ID because the name may change
        try:
            recipe = Recipe.objects.get(id=id)
        except:
            raise Exception("No recipe found by that ID")

        if ingredients and len(ingredients) > 150:
            raise Exception("A recipe may only have 150 ingredients")

        if steps and len(steps) > 200:
            raise Exception("A recipe may only have 200 ingredients")

        if name:
            recipe.name = name
        if photo:
            recipe.photo = photo

        if name or photo:
            recipe.save()
        # We just delete all the past ingredients and make new ones
        # We could make it more efficient by checking which have changed,
        # deleting all the excess ones, making a special case for no ingredients
        # ([] versus ommiting ingredients) and bulk updating
        # which would make this more efficient - I constructed it
        # and this is much simpler and more legible.
        # I prefer this because it is much simpler despite its obvious ineffeciency
        if ingredients:
            queryset = RecipeIngredient.objects.filter(recipe=recipe)
            for ing in queryset:
                ing.delete()
            for ing in ingredients:
                recipe.recipeingredient_set.create(
                    name=ing.name, quantity=ing.quantity, unit=ing.unit)

        # Process is more or less the same for ingredients
        if steps:
            queryset = RecipeStep.objects.filter(recipe=recipe)
            for step in queryset:
                step.delete()
            for step in steps:
                if step.order:
                    recipe.recipestep_set.create(
                        step=step.step,
                        order=step.order
                    )
                else:
                    recipe.recipestep_set.create(
                        step=step.step
                    )

        return UpdateRecipe(recipe=recipe)


class DeleteRecipe(graphene.Mutation):
    """Delete a recipe"""
    class Arguments:
        id = graphene.ID(required=False)
        name = graphene.String(required=False)

    recipe = graphene.Field(RecipeType)

    @classmethod
    @login_required
    def mutate(cls, root, info, id="", name=""):
        if id and name:
            raise Exception("Both a name and id cannot be provided")
        if not id and not name: 
            raise Exception("Either a name or an ID must be provided")
        try:
            if id:
                recipe = Recipe.objects.get(id=id)
            if name:
                recipe = Recipe.objects.get(name=name)
            _recipe = copy.deepcopy(recipe)
            recipe.delete()
            return DeleteRecipe(recipe=_recipe)
        except:
            raise Exception("No recipe found with that ID or name")

class Mutation(graphene.ObjectType):
    create_recipe = CreateRecipe.Field()
    update_recipe = UpdateRecipe.Field()
    delete_recipe = DeleteRecipe.Field()
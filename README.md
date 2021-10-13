# Table of Contents
1. [What is this?](#what-is-this?)
2. [How to run the repository](#how-to-run-the-repository)
3. [Data Structures](#data-structures)
4. [Queries and Mutations](#queries-and-mutations)
5. [Planned Changes](#planned-changes)
6. [Change Log](#change-log)

## What is this?

It's a Django-based, GraphQL-producing backend for a week's worth of groceries and recipes. Every week, my family plans out what we're going to eat and what we have to buy from the store. On this website, users can either have their own individual shopping list and groceries, or they can collaborate in a group. They have their own shopping list and meals for the week.

Other than that, there is one universal list of recipes. Everyone shares that list, can modify them and delete them. You could call it a social experiment, or, more simply, that I'm lazy and didn't want to think up a way to make them both editable, deletable and protected from trolls. The main motivtaion in this is that I'm envisioning the frontend making API requests to the translation website I made and that I don't want to use up too much of the free requests. Plus, it's probably only going to be used by my family and anyone who looks at my portfolio. But I can always access the Django admin panel to try to fix things if it really goes sideways.

As a warning, you can see the following things without even registering an account:
Group Members
Recipes

What you can't unless you're that user or in that group:
Personal/Group Shopping List
Personal/Group Meals
Requests to join a group (those made for the individual, those received for the group)

## How to run the repository
1. Clone/fork the repository
2. Configure the following environment variables:
> For the secret key:
> 1. DJANGO_SECRET_KEY
> 2. MY_EMAIL_ADDRESS (if you are allowing the messageMe mutation, which sends an email to this email address, some email integration will need to be configured)
> If you are running on your home environment and want to use your own database([Read the docs](https://docs.djangoproject.com/en/3.2/ref/databases/)):
> 1. AM_I_RUNNING_ON_MY_HOME_COMPUTER="true"
> 2. DATABASE_NAME
> 3. DATABASE_USER
> 4. DATABASE_HOST
> 5. DATABASE_PORT
> If you are running a Heroku integrated Postgres database (currently in use if AM_I_RUNNING_ON_MY_HOME_COMPUTER is not set/does not equal "true"):
> 1. DATABASE_URL
> If you are using the currently configured sendgrid integration:
> 1. SENDGRID_API_KEY
> 2. SENDGRID_EMAIL_FROM
> Note: I used Postgres for the database. Django config can take a variety of databases, including MongoDB. The Python packages/configuration for each of them can be quite different.
> Note: There's an email backend too. I used SendGrid, and any sort of implementation will take a sever amount of customization so I'm not going to include the details on this page. I will not include the SendGrid package, either, on the list to install below, but it can be found in the requirements.txt file.
> Note: Read the docs for django-graphql-auth for details about how to customize email templates. It's not particularly hard, but keep in mind that email supports little html/css, especially the cool stuff (for a good reason).
> 5. MY_EMAIL_ADDRESS if you want to use the messageMe mutation (cf mutations)

3. Open a terminal in the main folder and run:
    pip install -r requirements.txt

Or, individually, install these dependencies:

```
django
psycopg2
graphene-django
django-graphql-jwt
django-graphql-auth
```
Note: psycopg2 is python package to interact with postgresql databases. If want to use a different database, you will need a different package and to configure the database engine. At that point, you will have to probably change what environment variables you use.
4. Then run the following commands
```
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```
Note: The initial migration file has been made already, but you may need to make new migrations for the graphql jwt and graphql auth packages. If you have a problem with database stuff, you may need to reset your database, delete everything in the aww/migration folder EXCEPT __init__.py.
Note: You can also run python manage.py createsuperuser if you want to be able to access the admin panel at the /admin endpoint. All graphql functionality are handled at the /graphql endpoint.

## Data Structures
NOTE: Because these notes are so detailed for so simple an application, comments are few and far between, mostly to note 'why' decisions, not 'how'.

### Models (note that none of these have methods besides defining __str__ so the admin panel can be slightly more legible):

#### Abstracts (only classes with a meta subclass with abstract = True):
1. BaseIngredient:
> * id: UUID v4
> * name: CharField (max 100)
> * quantity: CharField (max 100) -- NOTE: This is a CharField because, as I have experienced with the translator, the quantity is often a string for cases like '1/4' and 'a few', etc besides the more obvious integer varieties.
> * unit: CharField (max: 50)
> NOTE: Though this is only addressed in those that inherit these classes, all of them are set to be deleted as soon as their ForeignKey (recipe, group or individual is deleted). 

2. BaseMeal:
> * id: UUID v4
> * day: Django Enum with the following values (Note: for a Django Enum, the possible values (i.e. Time.MONDAY) are the variable name. The second value (i.e. first in the tuple) is what is stored in the Database. The third value (i.e. second in the tuple) is what is output as its string equivalent, only visible in our application on the admin panel):
>> 1. MONDAY = "MON", "Monday"
>> 2. TUESDAY = "TUE", "Tuesday"
>> 3. WEDNESDAY = "WED", "Wednesday"
>> 4. THURSDAY = "THU", "Thursday"
>> 5. FRIDAY = "FRI", "Friday"
>> 6. SATURDAY = "SAT", "Saturday"
>> 7. SUNDAY = "SUN", "Sunday"
> * time: Django Enum with the following values:
>> 1. BREAKFAST = "B", "Breakfast"
>> 2. LUNCH = "L", "Lunch"
>> 3. DINNER = "D", "Dinner"
>> 4. OTHER = "O", "Other"
> NOTE: I was going to figure out how to make each day/time combination permutation unique to the item used as a ForeignKey on the inheriting class. That sounded like a lot of work that would require me to figure out a bunch of things that's more complicated than just saying unique=True, so I didn't do it
> * recipe: ForeignKey to a recipe (on recipe deletion, this field is set to null)
> * text: String (used as either addenda to a recipe or just the meal, i.e. 'Eat cheerios', 'Cook steak', etc.)
> NOTE: Though this is only addressed in those that inherit these classes, all of them are set to be deleted as soon as their ForeignKey (recipe, group or individual is deleted). 

#### Recipes
1. RecipeIngredient: inherits from BaseIngredient with a ForeignKey pointing to a Recipe
2. RecipeStep
> * id: UUID v4
> * step: TextField (text of the step)
> * order: IntegerField - if it is not provided, a signal function in aww.signal will provide one based the next available integer starting from 1.
3. Recipe:
> * id: UUID v4
> * name: CharField (max 200, unique)
> * photo: URLField (max 300, optional)
> * url: URLField (max 200, optional)
> NOTE: The url field of an ingredient is validated to be unique if it exists through a signal receiver called url_unique_if_exists -- it raises an IntegrityError if the URL exists but isn't unique. Unique=True doesn't work on this field because then it insists that only one recipe can be blank.
> NOTE: The ingredient and steps of the recipe can be found respectively at the attributes auto-generated by Django of recipeingredient_step and recipestep_set. This is how it is for all ForeignKeys in Django, so that it was why there isn't an explicit field pointing at the ingredients/steps/etc. Also, I could have changed the names of these fields, but I wanted the models to retain a more Django aspect to keep their appearances and that the prettier/human-readable names to be in the GraphQL types.

#### Groups:
1. GroupShoppingItem: inherits from BaseIngredient with a ForeignKey pointing to a Group
2. GroupMeal: inherits from BaseMeal with a ForeignKey pointing to a Group
3. Group:
> * id: UUID v4
> name: CharField (max 200, unique)
> members: ManyToManyField with Individual (a person may be in many groups, and a group may have many individuals in it)

#### Individuals (the difference between a User and an Individual will be explained below):
1. IndividualShoppingItem: inherits from BaseIngredient with a ForeignKey pointing to an Individual
2. IndividualMeal: inherits from BaseMeal with a ForeignKey pointing to an Individual
3. Individual:
> NOTE: The difference between a User and an Individual is that a User is created through a mutation (register) and carries a bunch of authentication-based information. Whenever a User is created through the register mutation, a corresponding Individual is created then attached to it through a OneToOneField. The Individual is accessible on the user through user.individual and the user is available on the individual at individual.user.
> * id: UUID v4
> * groups: ManyToManyField with Group (optional)
> * user: OneToOneField with User (on User deletion, the Individual is deleted too)

### GraphQL Types:

#### Django model-based Types:

##### RecipeStepType:
* Model: RecipeStep
* Fields: id, step, order (Django based model types' fields are from their corresponding model's values in these areas)

##### RecipeIngredientType:
* Model: RecipeIngredient
* Fields: id, name, quantity, unit

##### RecipeType:
* Model: Recipe
* Fields: id, name, photo, url
* Resolved Fields:
> 1. ingredients: returns the recipeingredient_set data on the corresponding recipe
> 2. steps: returns the recipestep_set data on the corresponding recipe

##### RequestType:
* Not based on a Django model
* Fields: id, name
* Note: This type is used both by groups when resolving all their join requests and individuals when when resolving all their requests made. 

##### GroupShoppingItemType
* Model: GroupShoppingItem
* Fields: id, name, quantity, unit

##### GroupMealType:
* Model: GroupMeal
* Fields: id, recipe, text, day, time, 

##### GroupsType (NOTE: this is a limited groups type compared to the GroupType below):
* Model: Group
* Fields: id, name
* Resolved Fields:
> 1. members: returns the emails of all the users in the group (as below, this isn't a normal field so that the ingredients/meals of each member cannot be further queried)
> 2. requests: returns the join_requests of the group as a List of RequestType

##### GroupType:
* Model: Group
* Fields: id, name
* Resolved Fields:
> 1. members: returns the usernames of all the users in the group
> 2. shopping_list: returns the groupshoppingitem_set on the corresponding Group
> 3. meals: returns the groupmeals_set on the corresponding Group

##### IndividualShoppingItemType
* Model: IndividualShoppingItem
* Fields: id, name, quantity, unit

##### IndividualMealType:
* Model: IndividualMeal
* Fields: id, recipe, text, day, time, 

##### IndividualType:
* Model: Individual
* Fields: id, groups
* Resolved Fields:
> 1. shopping_list: returns the individualshoppingitem_set on the corresponding Individual
> 2. meals: returns the individualmeals_set on the corresponding Individual
> 3. requests: returns the join_requests made by the user as a List of RequestType
> 4. email: returns the user.email property from the corresponding User
> 5. username: returns the user.username property from the corresponding User

#### Enums
NOTE: The values of the enums correspond with the values Django is expecting to put in the database, making it so I don't have to define a getter to do so.

##### Day:
> 1. MONDAY = "MON"
> 2. TUESDAY = "TUE"
> 3. WEDNESDAY = "WED"
> 4. THURSDAY = "THU"
> 5. FRIDAY = "FRI"
> 6. SATURDAY = "SAT"
> 7. SUNDAY = "SUN"

##### Time:
> 1. BREAKFAST = "B"
> 2. LUNCH = "L"
> 3. DINNER = "D"
> 4. OTHER = "O"

#### Input Types (graphene.ObjectType with listed fields):

##### IngredientInputType:
1. name: String
2. quantity: String
3. unit: string

##### RecipeStepInputType:
1. step: String
2. order: Integer (optional)

##### MealInputType:
1. text: String
2. recipeId: ID
3. day: Day (Enum listed above)
4. time: Time (Enum listed above)

## Queries and Mutations

### Queries:
1. recipes - retrieves a list of all recipes, returned as a list of RecipeType
2. groups - retrieves a list of all groups, returned as a list of GroupsType (severely limited compared to the GroupType so some semblance of privacy is kept)
3. recipe - retrieves a single recipe, returned as a RecipeType
> Variables:
> 1. id: ID - not required
> 2. name: String - not required
> NB: If both or neither are provided, an exception will be raised
4. individual - retrieves a single individual, returned as an IndividualType
> Variables:
> 1. id: ID - not required
> 2. name: String - not required
> NB: If both or neither are provided, an exception will be raised
> NB: This can only be accessed by a superuser. The purpose for this, combined with the below fact, is a quick replacement for looking up a user instead of going to the Dango dashboard.
> NB: This query is effectively useless and can be replaced by the MeQuery accessed with:
5. All individuals - retrieves all users and all details. Only accessible by a superuser. This is in case the admin doesn't want to access the admin panel.
6. group - retrieves a single group, returned as a GroupType
> Variables:
> 1. id: ID - not required
> 2. name: String - not required
> NB: If both or neither are provided, an exception will be raised
For example, a MeQuery (as referenced above) looks like the following:
```
query {
    me {
        individual {
            ...
        }
    }
}
```
[Read the docs](https://django-graphql-auth.readthedocs.io/en/latest/api/#mequery)

### Mutations
Note: all mutations require the user to log in, get a JWT then attach said to an Authorization header that reads JWT *cookie value* -- [Read the docs](https://django-graphql-auth.readthedocs.io/en/latest/quickstart/#insomnia-api-client). All group mutations (except createGroup) and inviteToGroup requires the logged in user's individual to be part of the group that's performing the aciton. All individual mutations perform the action on the logged-in user's individual.
1. Recipes:
> 1. createRecipe
>> * Variables:
>> 1. name: String
>> 2. photo: String (optional)
>> 3. ingedients: List of IngredientInputType (optional)
>> 4. steps: List of RecipeStepInputType (optional)
>> * Effect: attempt to create a recipe according to the instrument. There is a limit of 150 ingredients and 200 steps to a recipe. Of the recipes that I've seen, there are none that require more than 15 or so ingredients and 20ish max steps. So these limits feel incredibly generous. The mutation returns a RecipeType object.
>> * Returns: {recipe: RecipeType}
> 2. updateRecipe
>> * Variables:
>> 1. id: ID
>> 2. name: String (optional)
>> 3. photo: String (optional)
>> 4. ingedients: List of IngredientInputType (optional)
>> 5. steps: List of RecipeStepInputType (optional)
>> * Effect: attempt to find a recipe by the ID.
>> * Returns: {recipe: RecipeType}
> 3. deleteRecipe
>> * Variables:
>> 1. id: ID (optional)
>> 2. name: String (optional)
>> Note: An exception will be raised if both name and id or neither are provided
>> * Effect: attempt to find a recipe and delete it from the database
>> * Returns: {recipe: RecipeType} (copy of deleted recipe)

2. Groups:
> 1. createGroup
>> * Variables:
>> 1. name: String
>> * Effect: attempt to create a group with that name. If the name is already taken, a duplicate key error will arise. The first member of the group will be the individual making the request
>> * Returns: {individual: IndividualType, group: GroupType}
> 2. updateGroup:
>> * Variables:
>> 1. id: ID
>> 2. name: String (optional)
>> 3. shopping_list: List of IngredientInputType (optional)
>> 4. meals: List of MealInputType (optional)
>> * Effect: attempt to update the group with the current ID with the provided informatiom. The current shopping list and meals will be deleted, and new shopping list items/meals will be constructed from the given information. To avoid them being deleted, shopping_list or meals should not be provided. There is no way to empty these quantities out completely.
>> * Returns: {group: GroupType}
> 3. deleteGroup:
>> * Variables:
>> 1. id: ID
>> * Effect: attempt to delete the group with the ID. All individuals that are currently in that group will have the group removed from their groups.

3. Individuals:
> 1. updateIndividual:
>> * Variables:
>> 1. id: ID
>> 2. shopping_list: List of IngredientInputType (optional)
>> 3. meals: List of MealInputType (optional)
>> * Effect: attempt to update the user's shopping list and meals. The process is identical to the updateGroup methodology. Returns 
>> * Returns: {individual: IndividualType}
> 2. requestAccess:
>> * Variables:
>> 1. id: ID
>> * Effect: attempt to find group by ID. If successful, adds the group to the individual's group_requests and adds the individual to the group's join_requests. An exception will be raised if either of those lists contain the corresponding item already.
>> * Returns: {success: Boolean (always true since an exception will be raised otherwise), individual: IndividualType}
> 3. cancelRequest:
>> * Variables:
>> 1. id: ID
>> * Effect: attempt to find group by ID. If successful, remove the group from the individual's group_requests and removes the individual from the group's join_request. Raises an exception if the individual or the group doesn't have the other already in their corresponding list.
>> * Returns: {success: Boolean (always true since an exception will be raised otherwise), individual: IndividualType}
> 4. inviteToGroup:
>> * Variables
>> invitedId: ID
>> groupId: ID
>> * Effect: attempt to find group by ID. If unsuccessful, logged in user is not part of the group or invited user is already in the group, an exception will be raised. If the invited has a request to get in that group and/or if the group has a request to invite the new member, the individual and group will have the individual/group removed from their corresponding lists. Finally, the individual is added to the group and the group is added to the individual's groups.
>> * Returns: {individual: IndividualType, group: GroupType}
> 5. leaveGroup:
>> * Variables
>> id: ID (optional)
>> name: String (optional)
>> Note: if both or neither are provided, an exception will be raised.
>> * Effect: attempt to find group by ID. Logged in user's individual will be removed from the group and the group will be removed from individual's groups.
>> * Returns: {individual: IndividualType}

4. User
> 1. updateDetails
>> * Variables
>> email: String (optional)
>> username: String (optional)
>> * Effect: Updates the currently authenticated user's email and/or username as long as at least one is provided and the values are valid according to RegeX. The email uses the RC5322 standard, and username uses the standards for a Django username (max 150 characters, contains only letters/words/select special characters).

5. Other
> 1. messageMe
>> * Variables
>> message: String
>> name: String (optional)
>> * Effect: sends an email to the address at the environment variable MY_EMAIL_ADDRESS with the message provided. User's email is in the email title
>> * Returns: {success: Boolean}

## Planned Changes:
* Change types to nodes with Relay
* Sort new meals for individuals/groups based on day then mealtime

## Changelog:
1. 7/11/2021: Initial version of the backend
2. 7/13/2021: Added testing
3. 7/13/2021: I just added the message me mutation. It was simple.
4. 7/16/2021: Prep for deploy to Heroku
5. 7/18/2021: Changes are the following:
> 1. I corrected update recipe to not fail if the recipe has a url (no idea how my tests didn't cover that, but there is an explciitly a test for that now).
> 2. I added a few steps for validation that I'd previously thought to leave to the frontend, but it makes much more sense to do validation on the server side (as well). The changes are the following:
>> 1. Making sure that a recipe cannot change its URL on update
>> 2. Making sure that a meal has to have a unique time and day for each group or individual
> 3. I added a check that recipe steps are >= 1
> 4. Alongside that, I allowed recipe steps to not give their order. If it is left blank, the order will be the next available number in sequence, i.e.:
>> 1. Current step order: 1, 2, 3 - new step inserted at step 4
>> 2. Current step order: 2, 4, 6 - new step inserted at step 1
>> 3. Current step order: 1, 2, 5 - new step inserted at step 3
6. 7/22/2021: I forgot to set CORS headers. I used the django-cors-headers package.
7. 7/25/2021: I added a mutation (with corresponding tests) to allow a user to update their username and email address. I also changed it so group members are now identified by their usernames, not their email addresses. After this mutation changes the user details, a new token has to be issued.
8. 8/1/2021: Made it so blank arrays on updating individual/group deletes all previous values, also that meals for the update individual/group mutations are sorted when put into the database depending on day then time, starting from monday and breakfast.
9. 8/19/2021: Removed r2api from the dependencies. It should never have been included.
10. 8/23/2021: Fixed an error in the order of step generation where it work backwards from a gap to fill in the steps instead of work forwards from the last entry. Tests updated to account fo this.
11. 10/13/2021: Added Travis for CI and fixed the queries test. I didn't dockerize this because it is integrated with a Heroku Postgres instance.
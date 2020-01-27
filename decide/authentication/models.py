from django.db import models

# Create your models here.

from django.contrib.auth.models import AbstractUser

# AbstractUser already has the following fields and others.
# username, first_name, last_name
# email, password, groups


class CustomUser(AbstractUser):
    email1 = models.EmailField(max_length=254)
    email2 = models.EmailField(max_length=254)

    # to enforce required fields associated with
    # every user at registration
    # REQUIRED_FIELDS = ["email"]

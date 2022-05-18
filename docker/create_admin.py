#!/usr/bin/env python
import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "saap.settings")

def get_enviroment_admin_password(username):
    password = os.environ.get('ADMIN_PASSWORD')
    if not password:
        #print(
        #    "[CREATE_SUPERUSER] Environment variable $ADMIN_PASSWORD"
        #    " for user %s was not set. Leaving...\n" % username)
        sys.exit('MISSING_ADMIN_PASSWORD')
    return password

def create_superuser():
    from saap.core.models import User

    email = os.environ.get('ADMIN_EMAIL', '')

    if User.objects.filter(email=email).exists():
        #print("[CREATE_SUPERUSER] User %s already exists."
        #      " Exiting without change.\n" % email)
        sys.exit('ADMIN_USER_EXISTS')
    else:
        password = get_enviroment_admin_password(email)

        print("[CREATE_SUPERUSER] Creating superuser...\n")

        u = User.objects.create_superuser(
            email=email, password=password)
        u.save()

        print("[CREATE_SUPERUSE] Done.\n")

        sys.exit(0)

if __name__ == '__main__':
    django.setup()
    create_superuser()

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from apps.users.models import UserProfileTable
from allauth.account.signals import email_confirmed

User = get_user_model()

@receiver(post_save,sender =User)
def createprofile(sender,instance,created,**kwargs):
    if created:
        UserProfileTable.objects.create(user=instance)

@receiver(email_confirmed)
def activate_user(request, email_address, **kwargs):
    user = email_address.user
    user.is_active = True
    user.save()

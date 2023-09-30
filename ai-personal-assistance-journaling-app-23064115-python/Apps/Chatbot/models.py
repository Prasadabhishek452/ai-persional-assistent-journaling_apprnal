from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db import models
from .choices import *
import uuid
import datetime
import random
import jwt
from Automic_journal.settings import *
from django.utils import timezone
from django.conf import settings


class CommonTimePicker(models.Model):
    created_at = models.DateTimeField("Created Date", auto_now_add=True)
    updated_at = models.DateTimeField("Updated Date", auto_now=True)

    class Meta:
        abstract = True


class MyUserManager(BaseUserManager):

    def create_user(self, email, password):
        if not email:
            raise ValueError('Users must have an Email Address')

        user = self.model(
            email=self.normalize_email(email),
            is_active=False,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password):
        user = self.model(email=email)
        user.set_password(password)
        user.is_superuser = True
        if user.is_superuser:
            user.first_name = "Admin"
        user.is_active = True
        user.is_staff = True
        user.save(using=self._db)
        return user


class MyUser(AbstractBaseUser, CommonTimePicker):
    user_type = models.CharField("User Type", max_length=10, default='Admin', choices=USERTYPE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    email = models.EmailField("Email Address", null=True, blank=True, unique=True)
    mobile = models.CharField('Mobile Number', max_length=256)
    first_name = models.CharField("First Name", max_length=256, blank=True, null=True)
    last_name = models.CharField("Last Name", max_length=256, blank=True, null=True)
    avatar = models.ImageField("profile photo", null=True, blank=True,upload_to='user_images')
    gender = models.CharField("Gender", max_length=6, blank=True, choices=GENDER)
    age = models.DateField("Age", blank=True, null= True)
    otp = models.CharField('OTP', max_length=4, blank=True, null=True)
    device_token = models.CharField("Device ID", max_length=500, blank=True, null=True)
    created_by = models.CharField("Created by", max_length=256, blank=True, null=True)
    updated_by = models.CharField("Updated by", max_length=256, blank=True, null=True)
    is_superuser = models.BooleanField("Super User", default=False)
    is_staff = models.BooleanField("Staff", default=False)
    is_active = models.BooleanField("Active", default=False)
    description = models.TextField("Description", max_length=200, null=True, blank=True)
    form_completion_flag=models.BooleanField("form_completion_flag",default=False,blank=False)
    auth_provider=models.CharField("Auth Provider" , max_length=255, default="Email", choices=AUTH_PROVIDER, blank=True,null=True)
    email_verify = models.BooleanField("Email Verify", default=False)
    is_notification_on=models.BooleanField("is_notification_on",default=False)
    google_auth_id=models.CharField("google auth id",max_length=500,blank=True,null=True)
    email_exist_flag= models.BooleanField("email exist flag",default=False)
    facebook_auth_id=models.CharField("facebook auth id",max_length=500,blank=True,null=True)
    apple_auth_id=models.CharField("apple auth id",max_length=500,blank=True,null=True)
    
    objects = MyUserManager()
    USERNAME_FIELD = 'email'

    def __str__(self):
        return f"{self.uuid}_{self.email}" 
    
    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_superuser

    def get_short_name(self):
        return self.email

    def otp_creation(self):
        otp = random.randint(1000, 9999)
        self.otp = otp
        self.save()
        return otp

    def generate_jwt(self):
        payload = {
            'user_id': str(self.uuid),
            'email': self.email,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=1)  # Token expiration time
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def decode_jwt(token):
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            user_id = payload['user_id']
            return MyUser.objects.get(uuid=user_id)
        except (jwt.DecodeError, MyUser.DoesNotExist):
            return None

class UserDeviceTokenModel(CommonTimePicker):
    user_device=models.ForeignKey(MyUser,on_delete=models.CASCADE, related_name='user_device')
    device_type= models.CharField("device_type",max_length=10, blank=False, choices=DEVICE_TYPE)
    device_token=models.CharField("Device ID", max_length=500, blank=True, null=True)
    
    def __str__(self):
        return str(self.user_device)   

class UserIntrestModel(CommonTimePicker):
    name=models.CharField(max_length=200, null=True, blank=True)
    def __str__(self):
        return str(self.name)
    
class InterestModel(CommonTimePicker):
    intrest = models.ForeignKey(UserIntrestModel, on_delete=models.CASCADE,related_name='intrest')
    interest_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='interest_user')

    def __str__(self):
        return str(self.intrest.name)






class GoalModel(CommonTimePicker):
    goal_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='goal_user')
    goal_description = models.TextField("goal_description", max_length=200, null=True, blank=True) 
    goal_tittle = models.TextField("Goal Name", max_length=2000, null=True, blank=True)
    goal_image = models.ImageField("Goal photo", null=True, blank=True, upload_to='user_images')
    is_active=models.BooleanField("is_active",default=True,blank=False)
    is_completed=models.BooleanField("is_completed",default=False,blank=False)
    
    def __str__(self):
        return str(self.goal_tittle)

class GoalImagesModel(models.Model):
    goal_images=models.ForeignKey(GoalModel, on_delete=models.CASCADE,related_name='goal_images')
    image = models.ImageField("Goal photo", null=True, blank=True,upload_to='user_images')

class TaskModel(CommonTimePicker):
    task_goal=models.ForeignKey(GoalModel,on_delete=models.CASCADE,related_name='goal_task')
    task_tittle= models.CharField(max_length=200, null=True,blank=True)
    task_description= models.TextField("task_description", max_length=200, null=True, blank=True)
    task_start_time=models.DateTimeField("Start DateTime")
    is_active=models.BooleanField("is_active",default=True,blank=False)
    is_completed=models.BooleanField("is_completed",default=False,blank=False)
    task_duration = models.DurationField("Task Duration", null=True, blank=True)    


class DairyModel(CommonTimePicker):
    dairy_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='dairy_user')
    dairy_description = models.TextField("dairy_description", max_length=200, null=True, blank=True) 
    dairy_tittle = models.TextField("dairy Name", max_length=2000, null=True, blank=True)
    dairy_image = models.ImageField("dairy photo", null=True, blank=True,upload_to='user_images')
    
    def __str__(self):
        return str(self.dairy_tittle)

class DairyImagesModel(models.Model):
    dairy_images=models.ForeignKey(DairyModel, on_delete=models.CASCADE,related_name='dairy_images')
    image = models.ImageField("dairy photo", null=True, blank=True,upload_to='user_images')
    




class VisionModel(CommonTimePicker):
    vision_user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='vision_user')
    vision_description = models.TextField("vision_description", max_length=200, null=True, blank=True) 
    vision_tittle = models.TextField("Vision Name", max_length=2000, null=True, blank=True)
    vision_image = models.ImageField("Vision photo", null=True, blank=True,upload_to='user_images')
    
    def __str__(self):
        return str(self.vision_tittle)

class VisionImagesModel(models.Model):
    vision_images=models.ForeignKey(VisionModel, on_delete=models.CASCADE,related_name='vision_images')
    image = models.ImageField("Vision photo", null=True, blank=True,upload_to='user_images')






class StaticManagement(CommonTimePicker):
    static_tittle = models.CharField("static_tittle", max_length=200, null=True, blank=True)
    static_content = models.TextField("static_content", max_length=2000, null=True, blank=True)

    def __str__(self):
        return str(self.static_tittle)
    


class AchievementModel(CommonTimePicker):
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(max_length=200, null=True, blank=True)
    points = models.PositiveIntegerField()

    def __str__(self):
        return str(self.title)


class RewardModel(CommonTimePicker):
    achievement = models.ForeignKey(AchievementModel, on_delete=models.CASCADE, related_name='achievement_users')
    title = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(max_length=200, null=True, blank=True)
    points = models.PositiveIntegerField()

    def __str__(self):
        return str(self.title)


class UserAchievementRewardModel(CommonTimePicker):
    user = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='user_achievements_rewards')
    reward = models.ForeignKey(RewardModel, on_delete=models.CASCADE, related_name='reward_users')

    def __str__(self):
        return f"{self.user} - {self.achievement.title} - {self.reward.title}"


class UserFeedbackModel(CommonTimePicker):
    user_feedbacks=models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='user_feedbacks')
    stars=models.PositiveBigIntegerField()
    text=models.TextField("Feedback", max_length=2000, null=True, blank=True) 

class FeedbackImagesModel(models.Model):
    feedback_screenshots=models.ForeignKey(UserFeedbackModel, on_delete=models.CASCADE,related_name='feedback_screenshots')
    image = models.ImageField("Feedback photo", null=True, blank=True,upload_to='user_images')
    

    
class OnBoardModel(models.Model):
    first_title = models.CharField(max_length=200)
    first_dis = models.TextField(max_length=200)
    
    sec_title = models.CharField(max_length=200)
    sec_dis = models.TextField(max_length=200)
    
    third_title = models.CharField(max_length=200)
    third_dis = models.TextField(max_length=200)
    

class AboutAsmodel(models.Model):
    about_title = models.CharField(max_length=200)
    about_dis = models.TextField(max_length=200)
    
    terms_title = models.CharField(max_length=200)
    terms_dis = models.TextField(max_length=200)
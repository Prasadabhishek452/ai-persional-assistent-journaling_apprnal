from rest_framework import serializers
from django.conf import settings
from Apps.Chatbot.models import *
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from datetime import date
import re
api_settings = settings.REST_FRAMEWORK
from social_core.backends.google import GoogleOAuth2
from social_core.backends.facebook import FacebookOAuth2
from social_core.backends.apple import AppleIdAuth
from django.core.files.images import get_image_dimensions
from rest_framework import status
from .email import *




class UserDeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserDeviceTokenModel
        fields = ['device_type', 'device_token']

    def validate_device_type(self, value):
        if not value:
            raise serializers.ValidationError({"error":"Device type is required."})
        return value

    def validate_device_token(self, value):
        if not self.instance and not value:
            raise serializers.ValidationError({"error":"Device token is required."})
        return value

    def validate(self, attrs):
        for field_name, field_value in attrs.items():
            if self.fields[field_name].required and not field_value:
                raise serializers.ValidationError({"error":f"{field_name} cannot be empty"})
        
        return attrs
    
    
    
    
    
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True, allow_blank=False)
    password = serializers.CharField(required=True, allow_blank=False)
    device_type = serializers.ChoiceField(write_only=True,choices=DEVICE_TYPE,required=True)
    device_token = serializers.CharField(write_only=True,required=True, allow_blank=True)
    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password is required")
    
        # Password validation
        if len(value) < 6 or len(value) > 50:
            raise serializers.ValidationError("The length should be between 6 and 50 characters.")
        return value
    
    
    def validate_device_type(self, value):
        if not value:
            raise serializers.ValidationError("Device type cannot be empty")
        # Add additional validation rules for device_type if needed
        return value


    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        # Validate email format using regex
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise serializers.ValidationError({"error":"Invalid email format."})

        user = MyUser.objects.filter(email=email).first()
        if not user:
            raise serializers.ValidationError("User does not exist.")

        if not user.check_password(password):
            raise serializers.ValidationError("Incorrect password.")
        
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError(f"Unknown field: {', '.join(unknown_fields)}")

        
        attrs['user'] = user
        return attrs


    def create(self, validated_data):
        user = validated_data['user']
        device_type = validated_data.pop('device_type')
        device_token = validated_data.pop('device_token')


        if device_type and device_token:
                user_device_token = UserDeviceTokenModel(
                    user_device=user,
                    device_type=device_type, 
                    device_token=device_token)
                user_device_token.save()
        if device_type and not device_token:
            user_device_token = UserDeviceTokenModel(
                user_device=user,
                device_type=device_type,)
            user_device_token.save()
        # Generate JWT token for the user
        refresh = RefreshToken.for_user(user)
        token = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        if not user.email_verify:
            otp = user.otp_creation()
            send_otp_email(user.email, otp, user.first_name)

        # Return response with token and success message
        response = {
            'responsecode':status.HTTP_200_OK,
            'userid': user.id,
            'user_first_name': user.first_name,
            'singup_details_falgs':user.form_completion_flag,
            'email_varrified_flag':user.email_verify,
            'token': token,
            'responsemessage': 'User logged in successfully.',
        }
        return response





class UserVerifyEmailSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    def validate_otp(self, value):
        otp_str = str(value)
        if len(otp_str) != 4:
            raise serializers.ValidationError("OTP length must be 4 digits.")
        return value






class SignupSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True)
    device_type = serializers.ChoiceField(write_only=True, choices=DEVICE_TYPE)
    device_token = serializers.CharField(write_only=True, allow_blank=True)
    full_name = serializers.CharField(write_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)


    class Meta:
        model = MyUser
        fields = ['first_name', 'email', 'password', 'device_type', 'device_token','last_name','full_name']
        extra_kwargs = {
            'email': {'required': True},
            'device_token': {'required': True},
            'device_type': {'required': True},
        }
    


    def validate_password(self, value):
        if not value:
            raise serializers.ValidationError("Password is required")
    
        # Password validation
        if len(value) < 6 or len(value) > 50:
            raise serializers.ValidationError("The length should be between 6 and 50 characters.")
        return value
    

    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")
        return attrs

    def create(self, validated_data):
        email = validated_data.get('email')
        if MyUser.objects.filter(email=email).exists():
            raise serializers.ValidationError("User with this email already exists.")

        password = validated_data.pop('password')
        device_type = validated_data.pop('device_type')
        device_token = validated_data.pop('device_token')
        full_name = validated_data.pop('full_name')

        try:
            # Split the full_name into first_name and last_name
            first_name, *last_name_parts = full_name.split()
            last_name = ' '.join(last_name_parts)

            user = MyUser(is_active=True, first_name=first_name, last_name=last_name, **validated_data)
            user.set_password(password)
            user.save()

            if device_type and device_token:
                user_device_token = UserDeviceTokenModel(
                    user_device=user,
                    device_type=device_type,
                    device_token=device_token
                )
                user_device_token.save()
            elif device_type and not device_token:
                user_device_token = UserDeviceTokenModel(
                    user_device=user,
                    device_type=device_type
                )
                user_device_token.save()

            return user
        except Exception as e:
            print(e)
            raise serializers.ValidationError("Failed to create user")
   
   
   
    
from datetime import date
from django.core.exceptions import ValidationError
from rest_framework import serializers

class UserDetailsSerializer(serializers.Serializer):
    age = serializers.DateField(required=True)
    gender = serializers.CharField(required=True, allow_blank=False)
    interests = serializers.ListField(child=serializers.CharField(), required=True)
    avatar = serializers.ImageField(allow_empty_file=True, allow_null=True, required=False)

    def validate_age(self, value):
        if value > date.today():
            raise serializers.ValidationError("Age cannot be a future date.")
        return value

    def validate_gender(self, value):
        allowed_genders = ['Male', 'Female', 'Other']
        if value not in allowed_genders:
            raise serializers.ValidationError("Invalid gender. Allowed choices are Male, Female and Other.")
        return value

    def validate_interests(self, value):
        if not value:
            raise serializers.ValidationError({"error":"Interests cannot be an empty list."})
        return value

    def validate(self, attrs):
        print('running s', attrs)
        unknown_fields = set(self.get_initial()) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({"error":f"Unknown field(s): {', '.join(unknown_fields)}"})

        return attrs

    def create(self, validated_data):
        age = validated_data.get('age')
        gender = validated_data.get('gender')
        interests = validated_data.get('interests', [])
        avatar = validated_data.get('avatar')

        user = MyUser.objects.create(age=age, gender=gender, avatar=avatar, form_completion_flag=True)

        return user





class GetMyUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['description', 'avatar','first_name','last_name']
        read_only_fields = ['id', 'email']





class MyUserSerializer(serializers.ModelSerializer):
    full_name=serializers.CharField(max_length=255,required=False)
    description=serializers.CharField(max_length=2000,required=False)
    avatar=serializers.ImageField(required=False,allow_empty_file=True,allow_null=True)
    
    class Meta:
        model = MyUser
        fields = ['full_name', 'description', 'avatar']
        read_only_fields = ['id', 'email']

    def update(self, instance, validated_data):
        if not self.initial_data:
            raise serializers.ValidationError("Empty request body is not allowed.")

        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")

        full_name = validated_data.pop('full_name', None)
        if full_name:
            first_name, *last_name_parts = full_name.split()
            last_name = ' '.join(last_name_parts)
            print('full_name', first_name, last_name)
            instance.first_name = first_name
            instance.last_name = last_name

        
        print("avatar",validated_data.get('avatar', instance.avatar))
        print("description",validated_data.get('description', instance.description))
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.description = validated_data.get('description', instance.description)
        instance.save()

        response_data = {
            'full_name': f"{instance.first_name} {instance.last_name}",
            'description': instance.description,
            'avatar': instance.avatar,
        }
        print(response_data)
        return response_data









class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not value:
            raise serializers.ValidationError("Email is required")
         # Add additional validation rules for email if needed
        # You can use regular expressions or any other method to validate the email format
        # Example: Check if the email is in a valid format
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$', value):
            raise serializers.ValidationError("Invalid email format")
        try:
            user = MyUser.objects.get(email=value)
        except MyUser.DoesNotExist:
            raise serializers.ValidationError("Email does not exist.")

        return value
    
    
    

class VerifyOTPSerializer(serializers.Serializer):
    otp = serializers.IntegerField(required =True)
    user_id = serializers.IntegerField(required =True)

    def validate_otp(self, value):
        otp_str = str(value)
        if len(otp_str) != 4:
            raise serializers.ValidationError("OTP length must be 4 digits.")
        return value

    def validate_user_id(self, value):
        if value is None:
            raise serializers.ValidationError("User ID cannot be empty.")
        return value








class ReSendOTPSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required= True)

    def validate_user_id(self, value):
        if value is None:
            raise serializers.ValidationError("User ID cannot be empty.")

        try:
            user = MyUser.objects.get(id=value)
        except MyUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return user.email






class ResetPasswordSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate_user_id(self, value):
        try:
            user = MyUser.objects.get(id=value)
        except MyUser.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")
        return value

    def validate(self, attrs):
        password = attrs.get('password')
        confirm_password = attrs.get('confirm_password')

        if password != confirm_password:
            raise serializers.ValidationError("Passwords and confirm password do not match.")

        if not password:
            raise serializers.ValidationError("Password is required.")

        if not confirm_password:
            raise serializers.ValidationError("Confirm password is required.")

        # Password validation
        if len(password) < 6 or len(password) > 50:
            raise serializers.ValidationError("The length should be between 6 and 50 characters.")

        return attrs
    
    
    
    
    
    


class EditUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ['first_name', 'description', 'avatar']


    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.description = validated_data.get('description', instance.description)
        instance.avatar = validated_data.get('avatar', instance.avatar)
        instance.save()
        return instance




class StaticSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticManagement
        fields = '__all__'
        

class TaskModelSerializer(serializers.ModelSerializer):
    task_start_time = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S')
    task_goal = serializers.PrimaryKeyRelatedField(queryset=GoalModel.objects.all())

    class Meta:
        model = TaskModel
        fields = ['id', 'task_goal', 'task_tittle', 'task_description', 'task_start_time', 'is_active', 'is_completed', 'task_duration']
        extra_kwargs = {
            'task_tittle': {'required': True},
            'task_start_time': {'required': True},
        }

    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({"error":f"Unknown field(s): {', '.join(unknown_fields)}"})
        
        for field_name, field_value in attrs.items():
            if self.fields[field_name].required and not field_value:
                raise serializers.ValidationError({"error":f"{field_name} cannot be empty"})


        return attrs


class TaskSerializerrrr(serializers.ModelSerializer):
    class Meta:
        model = TaskModel
        fields = "__all__"

class GoalImagesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoalImagesModel
        fields = ['id', 'image']

class GoalModelSerializer(serializers.ModelSerializer):
    goal_images = GoalImagesModelSerializer(many=True, required=False)
    goal_image = serializers.ImageField(required=False)
    goal_task = TaskSerializerrrr(many=True, read_only=True)
    
    class Meta:
        model = GoalModel
        fields =  ['id', 'goal_user', 'goal_description', 'goal_tittle', 'goal_images', 'goal_image', 'is_active', 'is_completed', 'goal_task']
        read_only_fields = ['id', 'goal_user']
        extra_kwargs = {
            'goal_tittle': {'required': True},
            'goal_description': {'required': True},
        }

    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({"error":f"Unknown field(s): {', '.join(unknown_fields)}"})
        
        for field_name, field_value in attrs.items():
            if self.fields[field_name].required and not field_value:
                raise serializers.ValidationError({"error":f"{field_name} cannot be empty"})
        

        return attrs

    def create(self, validated_data):
        goal_images_data = self.context.get('request').FILES.getlist('goal_images')
        goal_image_data = self.context.get('request').FILES.get('goal_image')
        goal = GoalModel.objects.create(**validated_data)

        for image_data in goal_images_data:
            GoalImagesModel.objects.create(goal_images=goal, image=image_data)

        if goal_image_data:
            goal.goal_image = goal_image_data
            goal.save()

        return goal





class DairyImagesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DairyImagesModel
        fields = ['id', 'image']

class DairyModelSerializer(serializers.ModelSerializer):
    dairy_images = DairyImagesModelSerializer(many=True, required=False)

    class Meta:
        model = DairyModel
        fields = ['id', 'dairy_user', 'dairy_description', 'dairy_tittle', 'dairy_image', 'dairy_images']
        read_only_fields = ['id', 'dairy_user']
        extra_kwargs = {
            'dairy_tittle': {'required': True},
            'dairy_description': {'required': True},
            'dairy_image': {'required': False},
        }
    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({"error":f"Unknown field(s): {', '.join(unknown_fields)}"})
        for field_name, field_value in attrs.items():
            if self.fields[field_name].required and not field_value:
                raise serializers.ValidationError({"error":f"{field_name} cannot be empty"})
        return attrs

    def create(self, validated_data):
        dairy_images_data = self.context.get('request').FILES.getlist('dairy_images')
        dairy = DairyModel.objects.create(**validated_data)

        for image_data in dairy_images_data:
            DairyImagesModel.objects.create(dairy_images=dairy, image=image_data)

        return dairy
    


class VisionImagesModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VisionImagesModel
        fields = ['id', 'image']


class VisionModelSerializer(serializers.ModelSerializer):
    vision_images = VisionImagesModelSerializer(many=True, required=False)

    class Meta:
        model = VisionModel
        fields = ['id', 'vision_user', 'vision_description', 'vision_tittle', 'vision_image', 'vision_images']
        read_only_fields = ['id', 'vision_user']
        extra_kwargs = {
            'vision_tittle': {'required': True},
            'vision_description': {'required': True},
            'vision_image': {'required': False},
        }


    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({"error":f"Unknown field(s): {', '.join(unknown_fields)}"})
        for field_name, field_value in attrs.items():
            if self.fields[field_name].required and not field_value:
                raise serializers.ValidationError({"error":f"{field_name} cannot be empty"})
        return attrs

    def create(self, validated_data):
        vision_images_data = self.context.get('request').FILES.getlist('vision_images')
        vision = VisionModel.objects.create(**validated_data)

        for image_data in vision_images_data:
            VisionImagesModel.objects.create(vision_images=vision, image=image_data)

        return vision
    
class StaticSerializer(serializers.ModelSerializer):
    class Meta:
        model = StaticManagement
        fields = "__all__"
     

 


class FeedbackImagesSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackImagesModel
        fields = ('id',  'image')


class UserFeedbackSerializer(serializers.ModelSerializer):
    feedback_screenshots = FeedbackImagesSerializer(many=True, read_only=True)

    class Meta:
        model = UserFeedbackModel
        fields = ('id', 'user_feedbacks', 'stars', 'text', 'feedback_screenshots')
        read_only_fields = ('user_feedbacks','id',)  # Make user_feedbacks read-only
        extra_kwargs = {
            'stars': {'required': True},
            'text': {'required': True},
            'dairy_image': {'required': False},
        }
        
    def validate_stars(self, value):
        if not isinstance(value, int):
            raise serializers.ValidationError("Stars field must be an integer.")
        if value < 1 or value > 5:
            raise serializers.ValidationError("Stars field must be between 1 and 5.")
        return value

    def validate_text(self, value):
        if value is None or value.strip() == "":
            raise serializers.ValidationError("Text field cannot be empty.")
        return value
    
    def validate(self, attrs):
        unknown_fields = set(self.initial_data) - set(self.fields)
        if unknown_fields:
            raise serializers.ValidationError({"error":f"Unknown field(s): {', '.join(unknown_fields)}"})
        for field_name, field_value in attrs.items():
            if self.fields[field_name].required and not field_value:
                raise serializers.ValidationError(f"{field_name} cannot be empty")
        return attrs

    def create(self, validated_data):

        feedback_screenshots=self.context.get('request').FILES.getlist('feedback_screenshots')
        feedback = UserFeedbackModel.objects.create(**validated_data)
        for image_data in feedback_screenshots:
            FeedbackImagesModel.objects.create(feedback_screenshots=feedback, image=image_data)
        
        return feedback










#  --------------------------  user change password 

class UserChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, data):
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password != confirm_password:
            raise serializers.ValidationError("New password and confirm password do not match.")

        unknown_fields = set(data.keys()) - set(self.fields.keys())
        if unknown_fields:
            raise serializers.ValidationError(f"Unknown field(s): {', '.join(unknown_fields)}")

        for field_name, field in self.fields.items():
            if field.required and field_name not in data:
                raise serializers.ValidationError(f"{field_name} cannot be empty")

        return data

    def validate_new_password(self, value):
        if not value:
            raise serializers.ValidationError("Password is required")
    
        # Password validation
        if len(value) < 6 or len(value) > 50:
            raise serializers.ValidationError("The length should be between 6 and 50 characters.")
        return value
    

    
    
    
    
    
    
    
    
    
    
class UserIntrestModelSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = UserIntrestModel
        fields = '__all__'










    
class OnboradSerilazer(serializers.ModelSerializer):
    class Meta:
        model = OnBoardModel
        fields = "__all__"







class AboutAsSerilazer(serializers.ModelSerializer):
    class Meta:
        model = AboutAsmodel  # Corrected model name
        fields = "__all__"









       
        
class SocialLoginSerializer(serializers.Serializer):    

    google_auth_id = serializers.CharField(write_only=True,required=True,allow_blank=True)
    facebook_auth_id = serializers.CharField(write_only=True,required=True,allow_blank=True)
    apple_auth_id = serializers.CharField(write_only=True,required=True,allow_blank=True)
    device_token = serializers.CharField(write_only=True,required=True,allow_blank=True)
    email=serializers.EmailField(write_only=True,required=True,allow_blank=True)
    full_name=serializers.CharField(write_only=True,required=True,allow_blank=True)
    device_type = serializers.ChoiceField(write_only=True,required=True,choices=DEVICE_TYPE)
    auth_provider = serializers.ChoiceField(write_only=True,required=True,choices=AUTH_PROVIDER)
    avatar = serializers.ImageField(write_only=True,required=False,allow_empty_file=True, allow_null=True,)
    
    class Meta:
        fields = ['google_auth_id','facebook_auth_id','apple_auth_id','device_token','email','full_name','device_type','auth_provider','avatar']
    
    def validate(self, data):
        auth_provider = data.get('auth_provider')
        google_auth_id = data.get('google_auth_id')
        facebook_auth_id = data.get('facebook_auth_id')
        apple_auth_id = data.get('apple_auth_id')

        if auth_provider == 'google' and not google_auth_id:
            raise serializers.ValidationError("Google authentication ID is empty or not provided.")
        elif auth_provider == 'facebook' and not facebook_auth_id:
            raise serializers.ValidationError("Facebook authentication ID is empty or not provided.")
        elif auth_provider == 'apple' and not apple_auth_id:
            raise serializers.ValidationError("Apple authentication ID is empty or not provided.")

        return data
    def create(self, validated_data):
        auth_provider = validated_data.get('auth_provider')
        email = validated_data.get('email')
        device_type = validated_data.pop('device_type')
        device_token = validated_data.pop('device_token')
        full_name = validated_data.pop('full_name')
        avatar = validated_data.pop('avatar', None)

        user=False
        try:
            user= MyUser.objects.get(email=email)
        except Exception as e:
            print("Couldn't find user in profile for email")

        try:
            if auth_provider == 'google':
                google_auth_id = validated_data.get('google_auth_id')
                user= MyUser.objects.get(google_auth_id=google_auth_id)
        except Exception as e:
            print("Couldn't find user in profile for google_auth_id")
        try:
            if auth_provider == 'facebook':
                facebook_auth_id = validated_data.get('facebook_auth_id')
                user= MyUser.objects.get(facebook_auth_id=facebook_auth_id)
        except Exception as e:
            print("Couldn't find user in profile for facebook_auth_id")
        try:
            if auth_provider == 'apple':
                apple_auth_id = validated_data.get('apple_auth_id')
                user= MyUser.objects.get(apple_auth_id=apple_auth_id)
        except Exception as e:
            print("Couldn't find user in profile for apple_auth_id")

        try:
            if not user:
                # A new user was created
                first_name, *last_name_parts = full_name.split()
                last_name = ' '.join(last_name_parts)
                email_exist_flag = bool(email)
                # s3_file_name = 'user_images/' + avatar.name
                # avatar = upload_to_s3(avatar, s3_file_name)
                user=MyUser.objects.create(
                    first_name = first_name,
                    last_name = last_name, 
                    email_verify = email_exist_flag,
                    is_active = True,
                    email_exist_flag = email_exist_flag,
                    avatar = avatar,
                    **validated_data 
                )
        except Exception as e:
            print(e)
    

        try:
            user_device_token = UserDeviceTokenModel.objects.create(user_device=user, device_type=device_type, device_token=device_token)
        except Exception as e:
            # If there is an issue saving the user device token, we should delete the user to maintain data consistency.
            raise serializers.ValidationError(f"Signup failed")

        return user
           
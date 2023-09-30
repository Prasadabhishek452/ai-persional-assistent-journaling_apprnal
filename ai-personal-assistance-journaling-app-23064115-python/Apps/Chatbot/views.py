from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .models import *
from .serializers import *
from .email import *
from drf_yasg.utils import swagger_auto_schema
from rest_framework.throttling import UserRateThrottle , AnonRateThrottle
from rest_framework.parsers import MultiPartParser
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, PermissionDenied
from django.shortcuts import get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.views import exception_handler
from rest_framework.exceptions import Throttled
from django.contrib.auth import login
from social_django.utils import psa
from social_core.backends.google import GoogleOAuth2
from social_core.backends.facebook import FacebookOAuth2
from social_core.backends.apple import AppleIdAuth
from social_django.utils import load_strategy
from drf_yasg import openapi

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)  # Call the default exception handler

    if isinstance(exc, Throttled):
        custom_response_data = {
            'message': 'Request limit exceeded',
            'availableIn': f"{exc.wait} seconds"
        }
        response.data = custom_response_data

    return response





class EmailVerifyResendOTPView(APIView): 
    permission_classes = [IsAuthenticated,]

    # @swagger_auto_schema(
    #     # request_body=SendOTPSerializer,
    #     operation_description="Add Otp details",
    #     responses={
    #         200: "OTP re-sent successfully",
    #         400: "Bad Request",
    #         404: "Email does not exist",
    #     }
    # )
    def get(self, request):
        user = MyUser.objects.get(id=request.user.id)
        print(user)
        otp = user.otp_creation()
        send_otp_email(user.email, otp, request.user.first_name)
        return Response({'message': 'OTP sent successfully'})
    
    
    
class EmailVerifyResendOTPView(APIView): 
    permission_classes = [IsAuthenticated,]

    @swagger_auto_schema(
        operation_description="Add Otp details",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OTP re-sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_404_NOT_FOUND: openapi.Response(
                description="Email does not exist",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
        }
    )

    def get(self, request):
        user = MyUser.objects.get(id=request.user.id)
        print(user)
        otp = user.otp_creation()
        send_otp_email(user.email, otp, request.user.first_name)
        return Response({'responsemessage': 'OTP sent successfully', 'responsecode':status.HTTP_200_OK})
    
    
    
class UserEmailVerify(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        request_body=UserVerifyEmailSerializer,
        operation_description="Verify Email",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Email verification successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_429_TOO_MANY_REQUESTS: openapi.Response(
                description="Too Many Requests",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description="Internal Server Error",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
        }
    )
    def post(self, request):
        serializer = UserVerifyEmailSerializer(data=request.data)
        if serializer.is_valid():
            otp = serializer.validated_data['otp']
            user = MyUser.objects.get(id=request.user.id)

            if user.otp == str(otp):
                user.email_verify = True
                user.otp = None
                user.save()
                return Response({'responsemessage': 'Email verification successful','responsecode':status.HTTP_200_OK},status=status.HTTP_200_OK)
            else:
                return Response({'responsemessage': 'Email not verified. invalid OTP.','responsecode':status.HTTP_400_BAD_REQUEST},status=status.HTTP_400_BAD_REQUEST)
        else:
            print("--------------------------------",serializer.errors)
            otp_error= serializer.errors.get('otp')
            if 'otp' in serializer.errors and 'invalid' in otp_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": otp_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'otp' in serializer.errors and 'required' in otp_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "otp field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )



# -------------------------------------------------- LoginApi
class LoginApi(APIView):
    # permission_classes = [AllowAny,]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'device_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['ios', 'android', 'web'],
                ),
                'device_token': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'password', 'device_type', 'device_token'],
        ),
        operation_description="Add user details",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        # Include other response properties if needed
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        # Include other response properties if needed
                    },
                ),
            ),
        },
    )

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            response = serializer.create(serializer.validated_data)
            return Response(response)
        else:
            print("test -----------------------------------------------------",serializer.errors)
            email_error= serializer.errors.get('email')
            password_error= serializer.errors.get('password')
            device_type_error=serializer.errors.get('device_type')
            device_token_error=serializer.errors.get('device_token')
            non_field_error= serializer.errors.get('non_field_errors')
            
            if 'email' in serializer.errors and 'invalid' in email_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": email_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'email' in serializer.errors and 'blank' in email_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "Email field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            

            elif 'email' in serializer.errors and 'required' in email_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "Email field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'blank' in password_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "password field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'required' in password_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "password field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'invalid' in password_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage":  password_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_type' in serializer.errors and 'required' in device_type_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "device_type field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_type' in serializer.errors and 'invalid_choice' in device_type_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "device_type should be one of ios, android, web"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_type' in serializer.errors and 'blank' in device_type_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "device_type field may not be blank"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_token' in serializer.errors and 'required' in device_token_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "device_token field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'non_field_errors' in serializer.errors and 'invalid' in non_field_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": non_field_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            else:
                return Response(
                    {"responsecode": 400, "responsemessage": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )       











# -----------------------------------------------------      SignupAPIView
class SignupAPIView(APIView):
    # permission_classes = [AllowAny,]
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
                'password': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_PASSWORD),
                'device_type': openapi.Schema(type=openapi.TYPE_STRING, enum=['ios', 'android', 'web']),
                'device_token': openapi.Schema(type=openapi.TYPE_STRING),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['email', 'password', 'device_type'],
        ),
        responses={
            status.HTTP_201_CREATED: openapi.Response(
                description="User created successfully. An OTP has been sent to your email for verification.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "userid": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "token": openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                            "refresh": openapi.Schema(type=openapi.TYPE_STRING),
                            "access": openapi.Schema(type=openapi.TYPE_STRING),
                        }),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
            except serializers.ValidationError as e:
                error_detail = e.detail
                return Response(
                    {"responsecode": 400, "responsemessage": error_detail[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            refresh = RefreshToken.for_user(user)
            email = serializer.validated_data['email']
            # user = MyUser.objects.get(email=email)
            otp = user.otp_creation()
            send_otp_email(email, otp, user.first_name)
            token = {
                
                'refresh': str(refresh),
                'access': str(refresh.access_token)     
            }
            message = {
                "responsecode":status.HTTP_200_OK,
                "responsemessage": "User created successfully. An OTP has been sent to your email for verification.",
                "userid":user.id,
                "token":token
            }
            
            return Response(message, status=status.HTTP_201_CREATED)
        else:
            email_error= serializer.errors.get('email')
            device_type_error=serializer.errors.get('device_type')
            password_error=serializer.errors.get('password')
            device_token_error=serializer.errors.get('device_token')
            full_name_error=serializer.errors.get('full_name')
            non_field_error=serializer.errors.get('non_field_errors')
            if 'email' in serializer.errors and 'invalid' in email_error[0].code:
                email_error= serializer.errors.get('email')
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": email_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'email' in serializer.errors and 'blank' in email_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Email field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'email' in serializer.errors and 'required' in email_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Email field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_type' in serializer.errors and 'invalid_choice' in device_type_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_type should be one of ios, android, web."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_type' in serializer.errors and 'blank' in device_type_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_type field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_type' in serializer.errors and 'required' in device_type_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_type field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'blank' in password_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Password field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'required' in password_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Password field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'invalid' in password_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage":  password_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'device_token' in serializer.errors and 'required' in device_token_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_token field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'full_name' in serializer.errors and 'required' in full_name_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Full Name field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'full_name' in serializer.errors and 'blank' in full_name_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Full Name field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
            elif 'non_field_errors' in serializer.errors and 'invalid' in non_field_error[0].code:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": non_field_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )       


        
        
        
#  --------------------------  user change password 
class UserChangePasswordAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'current_password': openapi.Schema(type=openapi.TYPE_STRING),
                'new_password': openapi.Schema(type=openapi.TYPE_STRING),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['current_password', 'new_password', 'confirm_password'],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(description="OK - Password changed successfully."),
            status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad Request - Incorrect current password."),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(description="Internal Server Error - An error occurred."),
        }
    )

    def put(self, request):
        try:
            serializer = UserChangePasswordSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():

                user = request.user
                
                current_password = serializer.validated_data.get('current_password')
                new_password = serializer.validated_data.get('new_password')

                if not user.check_password(current_password):
                    return Response({'responsecode':status.HTTP_400_BAD_REQUEST,'responsemessage': 'Incorrect current password.'}, status=status.HTTP_400_BAD_REQUEST)

                # Set the new password
                user.set_password(new_password)
                user.save()

                return Response({'responsecode':status.HTTP_200_OK,'responsemessage': 'Password changed successfully.'}, status=status.HTTP_200_OK)
            else:

                current_password_error= serializer.errors.get('current_password')
                new_password_error= serializer.errors.get('new_password')
                confirm_password_error= serializer.errors.get('confirm_password')
                non_field_error= serializer.errors.get('non_field_errors')
                if 'current_password' in serializer.errors and 'invalid' in current_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": current_password_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'current_password' in serializer.errors and 'required' in current_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "current_password field is required"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'current_password' in serializer.errors and 'blank' in current_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "current_password field may not be blank."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'new_password' in serializer.errors and 'required' in new_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "new_password field is required"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'new_password' in serializer.errors and 'invalid' in new_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": new_password_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'new_password' in serializer.errors and 'blank' in new_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "new_password field may not be blank."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'confirm_password' in serializer.errors and 'required' in confirm_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "confirm_password field is required"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'confirm_password' in serializer.errors and 'invalid' in confirm_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": confirm_password_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'confirm_password' in serializer.errors and 'blank' in confirm_password_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "confirm_password field may not be blank."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'non_field_errors' in serializer.errors and 'invalid' in non_field_error[0].code:
                    return Response(
                        {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": non_field_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:   
                    return Response(
                            {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
        
        
        
        
        
        
        
        
        
        
        
# --------------------------------- UserDetailsAPIView
class UserDetailsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'age': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATE),
                'gender': openapi.Schema(type=openapi.TYPE_STRING, enum=['Male', 'Female', 'Other']),
                'interests': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING)),
                'avatar': openapi.Schema(type=openapi.TYPE_FILE),  # Use TYPE_FILE for image file
            },
            required=['age', 'gender', 'interests'],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="User details updated successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "userid": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "user_name": openapi.Schema(type=openapi.TYPE_STRING),
                        "userprofile": openapi.Schema(type=openapi.TYPE_STRING),
                        "singup_details_falgs": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                        "email_varrified_flag": openapi.Schema(type=openapi.TYPE_BOOLEAN),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    def post(self, request):
        serializer = UserDetailsSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            age = serializer.validated_data.get('age')
            gender = serializer.validated_data.get('gender')
            avatar = serializer.validated_data.get('avatar')
            print('running')
            user = request.user
            if not user:
                raise NotFound("User not found.")
            
            
            avatar = request.data.get('avatar')
            user.avatar = avatar
            user.age = age
            user.gender = gender
            user.form_completion_flag = True
            user.save()

            # Add interest
            interests = serializer.validated_data.get('interests')
            interests=interests[0]
            interests=interests.strip('[')
            interests=interests.strip(']')
            interests=interests.split(',')

            for interest_Name in interests:
                interest = InterestModel(intrest=UserIntrestModel.objects.get(id=interest_Name), interest_user=user)
                interest.save()

            responce={
                "responsemessage": 'User details updated successfully',
                "responsecode" : status.HTTP_200_OK,
                'userid': user.id,
                'user_name': user.first_name,
                'singup_details_falgs':user.form_completion_flag,
                'email_varrified_flag':user.email_verify,
                }
            return Response(responce, status=status.HTTP_200_OK)
        else:

            print("test -----------------------------------------------------",serializer.errors)
            age_error= serializer.errors.get('age')
            gender_error= serializer.errors.get('gender')
            interests_error=serializer.errors.get('interests')
            device_token_error=serializer.errors.get('device_token')
            non_field_error= serializer.errors.get('non_field_errors')
            
            if 'age' in serializer.errors and 'invalid' in age_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":age_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'age' in serializer.errors and 'required' in age_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":"age field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'gender' in serializer.errors and 'blank' in gender_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": gender_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'gender' in serializer.errors and 'invalid' in gender_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": gender_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'gender' in serializer.errors and 'required' in gender_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "gender field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'interests' in serializer.errors and 'required' in interests_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage": "interests field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"responsecode": 400, "responsemessage": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                ) 















# ------------------------------  SendOTPView
class SendOTPView(APIView):
    permission_classes = [AllowAny,]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_EMAIL),
            },
            required=['email'],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OK - OTP sent successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "user_id": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
                examples={'application/json': {'responsemessage': 'OTP sent successfully', 'responsecode': 200, 'user_id': 1}},
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request - Invalid email format or email does not exist.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
                examples={'application/json': {'responsemessage': 'Invalid email format', 'responsecode': 400}},
            ),
        }
    )
    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            try:
                user = MyUser.objects.get(email=email)
            except MyUser.DoesNotExist:
                raise serializers.ValidationError("Email does not exist.")

            otp = user.otp_creation()
            send_otp_reset_password(email, otp, user.first_name)

            return Response({'responsemessage': 'OTP sent successfully','responsecode':status.HTTP_200_OK,'user_id':user.id})
        else:
            print("test -----------------------------------------------------",serializer.errors)
            email_error= serializer.errors.get('email')
           
            if 'email' in serializer.errors and 'invalid' in email_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":email_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'email' in serializer.errors and 'required' in email_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":"email field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'email' in serializer.errors and 'blank' in email_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":"email field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"responsecode": 400, "responsemessage": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                ) 

















# ---------------------------------------- VerifyOTPView
class VerifyOTPView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [UserRateThrottle]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'otp': openapi.Schema(type=openapi.TYPE_INTEGER, format=openapi.FORMAT_INT32),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, format=openapi.FORMAT_INT32),
            },
            required=['otp', 'user_id'],
        ),
        operation_description="Verify OTP",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OTP verification successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_429_TOO_MANY_REQUESTS: openapi.Response(description="Too Many Requests"),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(description="Internal Server Error"),
        }
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():

            otp = serializer.validated_data['otp']
            user_id = serializer.validated_data['user_id']

            try:
                user = MyUser.objects.get(id=user_id)
            except:
                return Response({'responsecode':status.HTTP_400_BAD_REQUEST,'responsemessage': 'Invalid user id'},status=status.HTTP_400_BAD_REQUEST)

            if user.otp == str(otp):
                user.email_verify = True
                user.otp = None
                user.save()
                return Response({
                    'responsecode':status.HTTP_200_OK,
                    'responsemessage': 'OTP verification successful',
                    'singup_details_falgs':user.form_completion_flag,
                    'userid':user.id,'user_first_name': user.first_name,
                    'email_varrified_flag':user.email_verify,
                    },status=status.HTTP_200_OK)
            else:
                return Response({'responsecode':status.HTTP_400_BAD_REQUEST,'responsemessage': 'InVaild OTP'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            otp_error= serializer.errors.get('otp')
            user_id_error= serializer.errors.get('user_id')
            if 'otp' in serializer.errors and 'invalid' in otp_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": otp_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'otp' in serializer.errors and 'required' in otp_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "otp field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'user_id' in serializer.errors and 'required' in user_id_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "user_id field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'user_id' in serializer.errors and 'invalid' in user_id_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": user_id_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:   
                return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )





# -------------------------------------- ResendOTPView
class ResendOTPView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
            },
            required=['user_id'],
        ),
        operation_description="Add OTP details",
        responses={
            status.HTTP_200_OK: openapi.Response(description="OTP re-sent successfully"),
            status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad Request"),
            status.HTTP_404_NOT_FOUND: openapi.Response(description="User does not exist"),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(description="Internal Server Error"),
        }
    )
    def post(self, request):
        serializer = ReSendOTPSerializer(data=request.data)
        if serializer.is_valid():
            try:
                email = serializer.validated_data['user_id']
                user = MyUser.objects.get(email=email)
            except KeyError:
                raise APIException("Invalid data provided.", code=status.HTTP_400_BAD_REQUEST)
            except MyUser.DoesNotExist:
                raise APIException("User does not exist.", code=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                raise APIException("An error occurred.", code=status.HTTP_500_INTERNAL_SERVER_ERROR) from e

            otp = user.otp_creation()
            send_otp_reset_password(email, otp , user.first_name)
            return Response({'responsemessage': 'OTP re-sent successfully','responsecode':status.HTTP_200_OK}, status=status.HTTP_200_OK)
        else:
            print("test -----------------------------------------------------",serializer.errors)
            userid_error= serializer.errors.get('user_id')
           
            if 'user_id' in serializer.errors and 'invalid' in userid_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":userid_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'user_id' in serializer.errors and 'required' in userid_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":"user_id field is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'user_id' in serializer.errors and 'blank' in userid_error[0].code:
                return Response(
                    {"responsecode": 400, "responsemessage":"user_id field may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {"responsecode": 400, "responsemessage": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                ) 
    

    


    









class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER),
                'password': openapi.Schema(type=openapi.TYPE_STRING),
                'confirm_password': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['user_id', 'password', 'confirm_password'],
        ),
        operation_description="Reset password",
        responses={
            status.HTTP_200_OK: openapi.Response(description="Password reset successfully"),
            status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad Request"),
            status.HTTP_404_NOT_FOUND: openapi.Response(description="User does not exist"),
        }
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():

            user_id = serializer.validated_data.get('user_id')
            password = serializer.validated_data.get('password')

            try:
                user = MyUser.objects.get(id=user_id)
            except MyUser.DoesNotExist:
                raise APIException("User does not exist.", code=status.HTTP_404_NOT_FOUND)

            user.set_password(password)
            user.save()

            return Response({'responsecode':status.HTTP_200_OK,'responsemessage': 'Password reset successfully'}, status=status.HTTP_200_OK)
        else:
            password_error= serializer.errors.get('password')
            user_id_error= serializer.errors.get('user_id')
            confirm_password_error= serializer.errors.get('confirm_password')
            non_field_error= serializer.errors.get('non_field_errors')
            if 'password' in serializer.errors and 'invalid' in password_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": password_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'required' in password_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "password field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'password' in serializer.errors and 'blank' in password_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "password may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'user_id' in serializer.errors and 'required' in user_id_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "user_id field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'user_id' in serializer.errors and 'invalid' in user_id_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": user_id_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'confirm_password' in serializer.errors and 'required' in confirm_password_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "confirm_password field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'confirm_password' in serializer.errors and 'invalid' in confirm_password_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": confirm_password_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'confirm_password' in serializer.errors and 'blank' in confirm_password_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "confirm_password may not be blank."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'non_field_errors' in serializer.errors and 'invalid' in non_field_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": non_field_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:   
                return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )





# -------------------------------------------------- StaticManagementAPiView
class StaticManagementAPiView(APIView):

    # permission_classes = [AllowAny,]
    @swagger_auto_schema(
        operation_description="Static Content"
        )

    def get(self, request):
        try:
            static_obj = StaticManagement.objects.all()
            serializer = StaticSerializer(static_obj, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except GoalModel.DoesNotExist:
            return Response("Data not found", status=status.HTTP_404_NOT_FOUND)
        











# -------------------------------------------------- HomePageAPIView
class HomePageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get user's active goals, diarys, visions",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Successfully retrieved user's active goals, diary entries, and visions",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'responsemessage': openapi.Schema(type=openapi.TYPE_STRING),
                        'responsecode': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'userid': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'goals': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'diary_entries': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'visions': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad Request"),
            status.HTTP_404_NOT_FOUND: openapi.Response(description="User does not exist"),
        }
    )

    def get(self, request):
        try:
            user = request.user  # Assuming you have implemented authentication
            # Retrieve data for the user
            goals = GoalModel.objects.filter(goal_user=user)
            diary_entries = DairyModel.objects.filter(dairy_user=user)
            visions = VisionModel.objects.filter(vision_user=user)

            # Serialize the data
            goal_serializer = GoalModelSerializer(goals, many=True)
            diary_serializer = DairyModelSerializer(diary_entries, many=True)
            vision_serializer = VisionModelSerializer(visions, many=True)

            # Construct the response
            response_data = {
                'responsemessage':'data getting succesfully',
                'responsecode':status.HTTP_200_OK,
                'userid':user.id,
                'goals': goal_serializer.data,
                'diary_entries': diary_serializer.data,
                'visions': vision_serializer.data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'responsemessage': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
# TODO:request_body=GoalModelSerializer, check
# ----------------------------------------------------------  GoalModelAPIView
class GoalModelAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="see all goals",
        responses={
            200: "Successfully retrieved goals",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
        }
    )
    def get(self, request):
        goals = GoalModel.objects.filter(goal_user=request.user)
        serializer = GoalModelSerializer(goals, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        # request_body=GoalModelSerializer,
        operation_description="Add new goal",
        responses={
            201: "Successfully created a new goal",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
        }
    )
    def post(self, request):
        serializer = GoalModelSerializer(data=request.data, context={'request': request})
        obj_images = request.data.get('goal_images')
        obj_image = request.data.get('goal_image')

        
        if obj_images is not None and len(obj_images) == 0:
            raise serializers.ValidationError("goal_images list cannot be empty")
        if obj_image is not None and len(obj_image) == 0:
            raise serializers.ValidationError("goal_image list cannot be empty")

        if serializer.is_valid():
            serializer.save(goal_user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










# ---------------------------------------------- GoalModelDetailAPIView
class GoalModelDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=GoalModelSerializer,
        operation_description="Get, Edit, Delete Goal with ID",
        responses={
            200: "Successfully retrieved the goal",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Goal not found",
        }
    )
# not found
    def get_object(self, pk):
        return get_object_or_404(GoalModel, pk=pk, goal_user=self.request.user)

# get a single goal  
    def get(self, request, pk):
        goal = self.get_object(pk)
        serializer = GoalModelSerializer(goal)
        return Response(serializer.data)


# edit a goal 
    @swagger_auto_schema(
        request_body=GoalModelSerializer,
        operation_description="Edit a goal",
        responses={
            200: "Successfully edited the goal",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Goal not found",
        }
    )
    def put(self, request, pk):
        goal = self.get_object(pk)
        serializer = GoalModelSerializer(goal, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# delete a goal  
    @swagger_auto_schema(
        operation_description="Delete a goal",
        responses={
            204: "Successfully deleted the goal",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Goal not found",
        }
    )
    def delete(self, request, pk):
        goal = self.get_object(pk)
        goal.delete()
        return Response({"status":"goal deleted sucessfully"},status=status.HTTP_204_NO_CONTENT)


















# ----------------------------------------------- DairyModelAPIView
class DairyModelAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    @swagger_auto_schema(
        operation_description="Add new Dairy or see all Dairies",
        responses={
            200: "Successfully retrieved Dairies",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
        }
    )
    def get(self, request):
        dairies = DairyModel.objects.filter(dairy_user=request.user)
        serializer = DairyModelSerializer(dairies, many=True)
        return Response(serializer.data)

    # TODO: check the swagger for the api below
    @swagger_auto_schema(
        # request_body=DairyModelSerializer,
        operation_description="Add a new Dairy",
        responses={
            201: "Successfully created a new Dairy",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
        }
    )
    def post(self, request):
        serializer = DairyModelSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(dairy_user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)










# -----------------------------------------   DairyModelDetailAPIView
class DairyModelDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        request_body=DairyModelSerializer,
        operation_description="Get, Edit, Delete Dairy with ID",
        responses={
            200: "Successfully retrieved the Dairy",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Dairy not found",
        }
    )

    def get_object(self,  pk):
        return get_object_or_404(DairyModel, pk=pk, dairy_user=self.request.user)

    def get(self, pk):
        dairy = self.get_object(pk)
        if not dairy:
            return Response({'error': 'Dairy not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DairyModelSerializer(dairy)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=DairyModelSerializer,
        operation_description="Edit a Dairy",
        responses={
            200: "Successfully edited the Dairy",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Dairy not found",
        }
    )
    def put(self, request, pk):
        dairy = self.get_object(pk)
        serializer = DairyModelSerializer(dairy, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a Dairy",
        responses={
            204: "Successfully deleted the Dairy",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Dairy not found",
        }
    )
    def delete(self, request, pk):
        dairy = self.get_object(pk)
        dairy.delete()
        return Response({"status": "Dairy deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


        
        

# ----------------------------------------------- VisionModelAPIView
class VisionModelAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get all Visions",
        responses={
            200: "Successfully retrieved Visions",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
        }
    )
    def get(self, request):
        visions = VisionModel.objects.filter(vision_user=request.user)
        serializer = VisionModelSerializer(visions, many=True)
        return Response(serializer.data)


    # TODO: check the swagger for the api below
    @swagger_auto_schema(
        # request_body=VisionModelSerializer,
        operation_description="Add a new Vision",
        responses={
            201: "Successfully created a new Vision",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
        }
    )
    def post(self, request):
        serializer = VisionModelSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(vision_user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)








# -----------------------------------------------   VisionModelDetailAPIView
class VisionModelDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get, Edit, Delete Vision with ID",
        responses={
            200: "Successfully retrieved the Vision",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Vision not found",
        }
    )
    def get_object(self, pk):
        return get_object_or_404(VisionModel, pk=pk, vision_user=self.request.user)

    def get(self, request, pk):
        vision = self.get_object(pk)
        serializer = VisionModelSerializer(vision)
        return Response(serializer.data)

    # TODO: check the swagger for the api below
    @swagger_auto_schema(
        request_body=VisionModelSerializer,
        operation_description="Edit a Vision",
        responses={
            200: "Successfully edited the Vision",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Vision not found",
        }
    )
    def put(self, request, pk):
        vision = self.get_object(pk)
        serializer = VisionModelSerializer(vision, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a Vision",
        responses={
            204: "Successfully deleted the Vision",
            401: "Unauthorized - authentication credentials were not provided",
            403: "Permission Denied - user does not have permission to access this resource",
            404: "Vision not found",
        }
    )
    def delete(self, request, pk):
        vision = self.get_object(pk)
        vision.delete()
        return Response({"status": "Vision deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
    





# ------------------------------------------------- UserProfileAPIView
class UserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get User Profile",
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Successfully retrieved the User Profile",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'responsecode': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'responsemessage': openapi.Schema(type=openapi.TYPE_STRING),
                        'userid': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'description': openapi.Schema(type=openapi.TYPE_STRING),
                        'avatar': openapi.Schema(type=openapi.TYPE_STRING),
                        'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            status.HTTP_401_UNAUTHORIZED: openapi.Response(description="Unauthorized - authentication credentials were not provided"),
        }
    )
    def get(self, request):
        serializer = GetMyUserSerializer(request.user)
        first_name = serializer.data.get("first_name")
        last_name = serializer.data.get("last_name")
        if first_name and last_name:
            full_name = first_name + ' ' + last_name
        else:
            full_name = first_name or last_name
        data_to_send = {
            "responsecode":status.HTTP_200_OK,
            "responsemessage":"data getting sucessfully",
            "userid":request.user.id,
            "description": serializer.data.get("description"),
            "avatar": serializer.data.get("avatar"),
            "full_name":full_name
        }
        return Response(data_to_send, status=status.HTTP_200_OK)













# --------------------------------------- UpdateUserProfileAPIView
class UpdateUserProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyUserSerializer

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                'description': openapi.Schema(type=openapi.TYPE_STRING),
                'avatar': openapi.Schema(type=openapi.TYPE_FILE),
            },
            required=['full_name', 'description'],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="OK - User profile updated successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'responsecode': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'responsemessage': openapi.Schema(type=openapi.TYPE_STRING),
                        'userid': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'serialized_data': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'description': openapi.Schema(type=openapi.TYPE_STRING),
                                'avatar': openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad Request - Invalid or missing fields."),
        }
    )
    def put(self, request):
        serializer = self.serializer_class(request.user, data=request.data, partial=True)
        try:
            if serializer.is_valid():
                instance = serializer.save()
                serialized_data = MyUserSerializer(instance).data
                data={
                    "userid":request.user.id,
                    "responsecode":status.HTTP_200_OK,
                    "responsemessage":"user profile updated sucessfully",
                    "serialized_data":serialized_data
                }
                return Response(data)
            else:
                print("test -----------------------------------------------------",serializer.errors)
                full_name_error=serializer.errors.get('full_name')
                description_error= serializer.errors.get('description')
                avatar_error= serializer.errors.get('avatar')
                
                if 'full_name' in serializer.errors and 'invalid' in full_name_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":full_name_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'full_name' in serializer.errors and 'required' in full_name_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":"full_name field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'full_name' in serializer.errors and 'blank' in full_name_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":"full_name field may not be blank."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'description' in serializer.errors and 'blank' in description_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":"description field may not be blank."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'description' in serializer.errors and 'required' in description_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":"description field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'avatar' in serializer.errors and 'required' in avatar_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":"avatar field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'avatar' in serializer.errors and 'blank' in avatar_error[0].code:
                    return Response(
                        {"responsecode": 400, "responsemessage":"avatar field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    return Response(
                        {"responsecode": 400, "responsemessage": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    ) 
        except serializers.ValidationError as e:
            error_detail = e.detail
            return Response(
                {"responsecode": 400, "responsemessage": error_detail[0]},
                status=status.HTTP_400_BAD_REQUEST,
            )







# ------------------------------------------  UserTaskAPIView           
class UserTaskAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Get User Tasks",
        responses={
            200: "OK",
            401: "Unauthorized - authentication credentials were not provided",
        }
    )
    def get(self, request):
        tasks = TaskModel.objects.filter(task_goal__goal_user=request.user)
        serializer = TaskModelSerializer(tasks, many=True)
        return Response(serializer.data)









# ---------------------------------------  AddTaskAPIView
class AddTaskAPIView(APIView):
    @swagger_auto_schema(
        request_body=TaskModelSerializer,
        operation_description="Add Task",
        responses={
            201: "Created",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
        }
    )
    def post(self, request, goal_id):
        goal = GoalModel.objects.get(pk=int(goal_id), goal_user=request.user)
        task_data = request.data.copy()
        task_data['task_goal'] = goal.id
        serializer = TaskModelSerializer(data=task_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)







# ---------------------------------------     EditTaskAPIView
class EditTaskAPIView(APIView):
    @swagger_auto_schema(
        request_body=TaskModelSerializer,
        operation_description="Edit Task",
        responses={
            200: "OK",
            400: "Bad Request - request body is not valid",
            401: "Unauthorized - authentication credentials were not provided",
        }
    )
    def put(self, request, task_id):
        task = get_object_or_404(TaskModel, pk=int(task_id), task_goal__goal_user=request.user)
        task_data = request.data.copy()
        task_data['task_goal'] = task.task_goal.id  # Preserve the original goal ID
        serializer = TaskModelSerializer(task, data=task_data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)











# ------------------------------------------------------  ApiViewStaticManagement
# TODO: request_body=StaticSerializer, check
class ApiViewStaticManagement(APIView):
    # parser_classes = [AllowAny,]
    @swagger_auto_schema(
        # request_body=StaticSerializer,
        operation_description="Get static data",

    )
    def get(self, request):
        static_obj = StaticManagement.objects.all()
        serializer = StaticSerializer(static_obj, many=True)
        return Response(serializer.data,status=status.HTTP_200_OK)
    





class UserFeedbackAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Get user feedbacks",
        responses={
            200: openapi.Response(
                description="OK - Retrieved user feedbacks successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'responsecode': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'responsemessage': openapi.Schema(type=openapi.TYPE_STRING),
                        'user_feedbacks': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'user_feedbacks': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'stars': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'text': openapi.Schema(type=openapi.TYPE_STRING),
                                    'feedback_screenshots': openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(
                                            type=openapi.TYPE_OBJECT,
                                            properties={
                                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                                'image': openapi.Schema(
                                                    type=openapi.TYPE_STRING,
                                                    format=openapi.FORMAT_BINARY
                                                ),
                                            }
                                        )
                                    ),
                                }
                            )
                        ),
                    }
                )
            ),
        }
    )
  
    def get(self, request):
        feedbacks = UserFeedbackModel.objects.filter(user_feedbacks=request.user)
        serializer = UserFeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        request_body=UserFeedbackSerializer,
        responses={
            201: openapi.Response(
                description="Created - User feedback created successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsedata": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'user_feedbacks': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'stars': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'text': openapi.Schema(type=openapi.TYPE_STRING),
                                'feedback_screenshots': openapi.Schema(
                                    type=openapi.TYPE_ARRAY,
                                    items=openapi.Schema(
                                        type=openapi.TYPE_OBJECT,
                                        properties={
                                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                            'image': openapi.Schema(
                                                type=openapi.TYPE_STRING,
                                                format=openapi.FORMAT_BINARY
                                            ),
                                        }
                                    )
                                ),
                            }
                        ),
                    }
                ),
            ),
            400: openapi.Response(description="Bad Request - Invalid data"),
            500: openapi.Response(description="Internal Server Error - Failed to create user feedback"),
        }
    )
    def post(self, request):
        serializer = UserFeedbackSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user_feedbacks=request.user)
            response={
                "responsecode": status.HTTP_200_OK,
                "responsemessage": "User feedback created successfully",
                "responsedata": serializer.data
            }
            return Response(response, status=status.HTTP_201_CREATED)

        else:
            print(serializer.errors)
            stars_error= serializer.errors.get('stars')
            text_error= serializer.errors.get('text')
            if 'stars' in serializer.errors and 'invalid' in stars_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": stars_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'stars' in serializer.errors and 'required' in stars_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "stars field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'text' in serializer.errors and 'required' in text_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": "text field is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            elif 'text' in serializer.errors and 'invalid' in text_error[0].code:
                return Response(
                    {"responsecode":status.HTTP_400_BAD_REQUEST, "responsemessage": text_error[0]},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:   
                return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
       







class UserFeedbackDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(UserFeedbackModel, pk=pk, user_feedbacks=self.request.user)


    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="OK - Retrieved user feedback details successfully.",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'user_feedbacks': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'stars': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'text': openapi.Schema(type=openapi.TYPE_STRING),
                        'feedback_screenshots': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                    'image': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY),
                                }
                            )
                        ),
                    }
                )
            ),
            404: openapi.Response(description="Not Found - Feedback not found."),
        }
    )
    def get(self, request, pk):
        feedback = self.get_object(pk)
        if not feedback:
            return Response({'error': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserFeedbackSerializer(feedback)
        return Response(serializer.data)

    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'stars': openapi.Schema(type=openapi.TYPE_INTEGER),
                'text': openapi.Schema(type=openapi.TYPE_STRING),
                'feedback_screenshots': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Schema(type=openapi.TYPE_FILE, format=openapi.FORMAT_BINARY),
                ),
            },
            required=['stars', 'text'],
        ),
        responses={
            200: openapi.Response(description="OK - User feedback updated successfully."),
            400: openapi.Response(description="Bad Request - Invalid or missing fields."),
            404: openapi.Response(description="Not Found - Feedback not found."),
            500: openapi.Response(description="Internal Server Error - An error occurred."),
        }
    )
    def put(self, request, pk):
        feedback = self.get_object(pk)
        if not feedback:
            return Response({'error': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserFeedbackSerializer(feedback, data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    
    @swagger_auto_schema(
        responses={
            204: openapi.Response(description="No Content - Feedback deleted successfully."),
            404: openapi.Response(description="Not Found - Feedback not found."),
            500: openapi.Response(description="Internal Server Error - An error occurred."),
        }
    )
    def delete(self, request, pk):
        feedback = self.get_object(pk)
        if not feedback:
            return Response({'error': 'Feedback not found.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            feedback.delete()
            return Response({'message': 'Feedback deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        


# ---------------------------------- User notification 

class UserNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        responses={
            200: "OK - Retrieved user notification status successfully",
            404: "Not Found - User not found",
            500: "Internal Server Error - Failed to retrieve user notification status",
        }
    )
    def get(self, request):
        try:
            user = MyUser.objects.get(id=request.user.id)
            if user:
                return Response({"notification_status": user.is_notification_on}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except MyUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'is_notification_on': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
            required=['is_notification_on'],
        ),
        responses={
            200: openapi.Response(description="OK - Updated notification status successfully."),
            400: openapi.Response(description="Bad Request - Invalid or missing fields."),
            404: openapi.Response(description="Not Found - User not found."),
            500: openapi.Response(description="Internal Server Error - An error occurred."),
        }
    )

    def put(self, request):
        
        try:
            user = MyUser.objects.get(id=request.user.id)
            is_notification_on = request.data.get('is_notification_on')

            if is_notification_on is None:
                return Response({'error': 'is_notification_on field is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(is_notification_on, bool):
                return Response({'error': 'is_notification_on field must be a boolean value.'}, status=status.HTTP_400_BAD_REQUEST)
            
            if len(request.data.keys()) > 1:
                return Response({'error': 'Additional fields are not allowed.'}, status=status.HTTP_400_BAD_REQUEST)
            
            user.is_notification_on = is_notification_on
            user.save()
            
            return Response({'notification_status': user.is_notification_on}, status=status.HTTP_200_OK)
        except MyUser.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class LogOutApiView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'device_token': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['device_token'],
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(description="OK - Logout sucessfully"),
            status.HTTP_400_BAD_REQUEST: openapi.Response(description="Bad Request - Invalid data"),
            status.HTTP_404_NOT_FOUND: openapi.Response(description="Not Found - Invalid userToken or Token does not exist"),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(description="Internal Server Error - An error occurred"),
        }
    )
    def post(self, request):
        device_token = request.data.get('device_token')

        if device_token is None:
            return Response({'responsecode':status.HTTP_404_NOT_FOUND,'responsemessage': 'device_token field is required.'}, status=status.HTTP_404_NOT_FOUND)
        try:
            if device_token == "":
                # Perform the necessary actions for a blank device_token
                # ...
                return Response({'responsecode':status.HTTP_200_OK,'responsemessage': 'Logout sucessfully'}, status=status.HTTP_200_OK)
            else:
                # Delete the user's token associated with the provided device token
                user_device_token = UserDeviceTokenModel.objects.filter(device_token=device_token, user_device=request.user)
                user_device_token.delete()
                return Response({'responsecode':status.HTTP_200_OK,'responsemessage': 'Logout sucessfully'}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'responsecode':status.HTTP_404_NOT_FOUND,'responsemessage': 'Token does not exist'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'responsecode':status.HTTP_500_INTERNAL_SERVER_ERROR,'responsemessage': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    
class UserIntrestModelAPIView(APIView):
    def get(self, request):
        try:
            user_interests = UserIntrestModel.objects.all()
            serializer = UserIntrestModelSerializer(user_interests, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            serializer = UserIntrestModelSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










class UserIntrestModelAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        try:
            user_interests = UserIntrestModel.objects.all()
            serializer = UserIntrestModelSerializer(user_interests, many=True)
            data = {
            "responsecode": status.HTTP_200_OK,
            "responsemessage":"data getting sucessfully",
            "user_interests":serializer.data
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        try:
            name = request.data.get('name')

            if not name:
                return Response({'error': 'name is required cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

            serializer = UserIntrestModelSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class UserIntrestModelDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    @swagger_auto_schema(
        operation_description="Get all interests",
        responses={
            200: openapi.Response(
                description="OK - Successfully retrieved user interests",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "user_interests": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                "id": openapi.Schema(type=openapi.TYPE_INTEGER),
                                "name": openapi.Schema(type=openapi.TYPE_STRING),
                            }),
                        ),
                    },
                ),
            ),
            500: openapi.Response(description="Internal Server Error - An error occurred."),
        }
    )
    def get_object(self, pk):
        try:
            return UserIntrestModel.objects.get(pk=pk)
        except:
            return Response({'message': 'User interest not found.'}, status=status.HTTP_404_NOT_FOUND)


    
    def get(self, request, pk):
        try:
            user_interest = self.get_object(pk)
            serializer = UserIntrestModelSerializer(user_interest)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'message': 'User interest not found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        try:
            user_interest = self.get_object(pk)
            serializer = UserIntrestModelSerializer(user_interest, data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except UserIntrestModel.DoesNotExist:
            return Response({'message': 'User interest not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': 'User interest not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            user_interest = self.get_object(pk)
            user_interest.delete()
            return Response({"status":"interest deleted sucessfully"},status=status.HTTP_200_OK)
        except UserIntrestModel.DoesNotExist:
            return Response({'message': 'User interest not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'message': 'User interest not found'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

















class RefreshTokenView(APIView):
    # permission_classes = [AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'refresh_token': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='The refresh token for obtaining a new access token.',
                ),
            },
            required=['refresh_token'],  # Array of required properties
        ),
        responses={
            status.HTTP_200_OK: openapi.Response(
                description="Access token refreshed successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "access_token": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_400_BAD_REQUEST: openapi.Response(
                description="Bad Request - Invalid request",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: openapi.Response(
                description="Internal Server Error - Failed to refresh access token",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "responsemessage": openapi.Schema(type=openapi.TYPE_STRING),
                        "responsecode": openapi.Schema(type=openapi.TYPE_INTEGER),
                    },
                ),
            ),
        }
    )
    

    def post(self, request):
        refresh_token = request.data.get('refresh_token')

        if not refresh_token:
            return Response({'responsemessage': 'Refresh token is required','responsecode':status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

        if refresh_token.strip() == '':
            return Response({'responsemessage': 'Refresh token cannot be empty','responsecode':status.HTTP_400_BAD_REQUEST}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
            return Response({'access_token': access_token,'responsemessage':'success','responsecode':status.HTTP_200_OK})
        except Exception as e:
            return Response({'responsemessage': 'Invalid refresh token','responsecode':status.HTTP_500_INTERNAL_SERVER_ERROR}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
   










# TODO: request_body=StaticSerializer, check
class ApiViewOnboard(APIView):
    # parser_classes = [AllowAny,]
    @swagger_auto_schema(
        # request_body=StaticSerializer,
        operation_description="Get static data",
        responses={
            status.HTTP_200_OK: openapi.Response(description="OK - Static data retrieved successfully."),
        }
    )
    def get(self, request):
        static_obj = OnBoardModel.objects.all()
        serializer = OnboradSerilazer(static_obj, many=True)
        data = {
            "responsecode": status.HTTP_200_OK,
            "responsemessage":"data getting sucessfully",
            "static_data":serializer.data
        }
        return Response(data,status=status.HTTP_200_OK)




class ApiViewAboutUs(APIView):
    # parser_classes = [AllowAny,]
    @swagger_auto_schema(
        # request_body=StaticSerializer,
        operation_description="Get static data",

    )
    def get(self, request):
        static_obj = AboutAsmodel.objects.all()
        serializer = AboutAsSerilazer(static_obj, many=True)
        data = {
            "responsecode": status.HTTP_200_OK,
            "responsemessage":"data getting sucessfully",
            "About_us_data":serializer.data
        }
        return Response(data,status=status.HTTP_200_OK)
    
    
    


class SocialLoginView(APIView):
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'google_auth_id': openapi.Schema(type=openapi.TYPE_STRING),
                'facebook_auth_id': openapi.Schema(type=openapi.TYPE_STRING),
                'apple_auth_id': openapi.Schema(type=openapi.TYPE_STRING),
                'device_token': openapi.Schema(type=openapi.TYPE_STRING),
                'email': openapi.Schema(type=openapi.TYPE_STRING),
                'full_name': openapi.Schema(type=openapi.TYPE_STRING),
                'device_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['android', 'ios', 'web'],

                ),
                'auth_provider': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=['google', 'facebook', 'apple'],
                ),
                'avatar': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_BINARY),
            },
            required=['google_auth_id', 'facebook_auth_id', 'apple_auth_id', 'device_token', 'email', 'full_name', 'device_type', 'auth_provider', 'avatar'],
        ),
        responses={
            200: openapi.Response(
                description='User login successful',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'user_id': openapi.Schema(type=openapi.TYPE_STRING),
                        'token': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'access': openapi.Schema(type=openapi.TYPE_STRING),
                            },
                        ),
                    },
                ),
            ),
            400: openapi.Response(
                description='Signup failed',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                        'errors': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            500: openapi.Response(
                description='Internal server error',
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'message': openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
        },
    )
    
    
    
    def post(self,request):
        try:
            serializer=SocialLoginSerializer(data=request.data)
            if serializer.is_valid():
                user=serializer.save()
                refresh=RefreshToken.for_user(user)
                token={
                    'refresh': str(refresh),
                    'access': str(refresh.access_token)
                }
                response_data={
                    "responsecode": status.HTTP_200_OK,
                    'responsemessage': 'User login successfull',
                    'user_first_name': user.first_name,
                    'userid': user.id,
                    'singup_details_falgs':user.form_completion_flag,
                    'email_varrified_flag':user.email_verify,
                    'email_exist_flag':user.email_exist_flag,
                    'token': token  # Generate JWT token for authentication
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                print("--------------------------------",serializer.errors)
                email_error= serializer.errors.get('email')
                device_type_error= serializer.errors.get('device_type')
                auth_provider_error= serializer.errors.get('auth_provider')
                non_field_error= serializer.errors.get('non_field_errors')
                full_name_error= serializer.errors.get('full_name')
                apple_auth_id_error= serializer.errors.get('apple_auth_id')
                google_auth_id_error= serializer.errors.get('google_auth_id')
                facebook_auth_id_error= serializer.errors.get('facebook_auth_id')
                device_token_error= serializer.errors.get('device_token')
                if 'email' in serializer.errors and 'invalid' in email_error[0].code:

                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": email_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'email' in serializer.errors and 'blank' in email_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Email field may not be blank."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'email' in serializer.errors and 'required' in email_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "Email field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                    
                elif 'device_type' in serializer.errors and 'required' in device_type_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_type field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'device_type' in serializer.errors and 'invalid_choice' in device_type_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_type should be one of ios, android, web."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                    
                elif 'auth_provider' in serializer.errors and 'required' in auth_provider_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "auth_provider field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'auth_provider' in serializer.errors and 'invalid_choice' in auth_provider_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "auth_provider should be one of facebook, apple, google."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                elif 'non_field_errors' in serializer.errors and 'invalid' in non_field_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": non_field_error[0]},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                elif 'full_name' in serializer.errors and 'required' in full_name_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "full_name field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'apple_auth_id' in serializer.errors and 'required' in apple_auth_id_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "apple_auth_id field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'facebook_auth_id' in serializer.errors and 'required' in facebook_auth_id_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "facebook_auth_id field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'google_auth_id' in serializer.errors and 'required' in google_auth_id_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "google_auth_id field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                elif 'device_token' in serializer.errors and 'required' in device_token_error[0].code:
                    return Response(
                        {"responsecode": status.HTTP_400_BAD_REQUEST, "responsemessage": "device_token field is required."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                    
                else:
                    return Response(
                        {"responsecode": 400, "responsemessage": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            
        except serializers.ValidationError as e:
            if isinstance(e.detail, dict):
                error_message = e.detail.get('non_field_errors') or e.detail
            elif isinstance(e.detail, list):
                error_message = ', '.join(e.detail)
            else:
                error_message = str(e)
                print(error_message)
                
            response_data = {
                'responsecode': status.HTTP_400_BAD_REQUEST,
                'responsemessage': error_message
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)


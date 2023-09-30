from django.urls import path
from .views import *
from rest_framework import permissions
from django.conf.urls.static import static
from django.conf import settings
urlpatterns = [
    #------------------------ Signup url ----------------------------------#
    path('user/signup/', SignupAPIView.as_view(), name='signup'),                                                 
    path('user/signup/signup-details', UserDetailsAPIView.as_view(), name='signup-details'),
    
    path('user/social-login/', SocialLoginView.as_view(), name='social_login'),

    path('token/refresh/', RefreshTokenView.as_view(), name='refresh-token'),
    
    path('user/verify-email', UserEmailVerify.as_view(), name='verify-email'),                                            
    path('user/resend-verify-otp-email', EmailVerifyResendOTPView.as_view(), name='resend-verify-otp-email'),    
    path('user/login', LoginApi.as_view(), name="login-api"),
    path('user/logout', LogOutApiView.as_view(), name="logout-api"),
    path('user/forgot-pasword', SendOTPView.as_view(), name='send_otp'),
    path('user/verify-otp', VerifyOTPView.as_view(), name='verify_otp'),
    path('user/resend-otp', ResendOTPView.as_view(), name='resend_otp'),
    path('user/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    
    #------------------------ Home page ------------------------------------#
    path('home',HomePageAPIView.as_view(), name='home'),
    
    path('goals', GoalModelAPIView.as_view(), name='goal-list'),
    path('goals/<int:pk>', GoalModelDetailAPIView.as_view(), name='goal-detail'),
    
    path('dairies', DairyModelAPIView.as_view(), name='dairy-list'),
    path('dairies/<int:pk>', DairyModelDetailAPIView.as_view(), name='dairy-detail'),
    
    path('visions', VisionModelAPIView.as_view(), name='vision-list'),
    path('visions/<int:pk>', VisionModelDetailAPIView.as_view(), name='vision-detail'),
    
    path('user/tasks/', UserTaskAPIView.as_view(), name='user-tasks'),
    
    path('goals/<int:goal_id>/add-task/', AddTaskAPIView.as_view(), name='add-task'),
    
    path('tasks/<int:task_id>/edit/', EditTaskAPIView.as_view(), name='edit-task'),
    
    path('user/profile', UserProfileAPIView.as_view(), name='user-profile'),

    path('user/profile/update/', UpdateUserProfileAPIView.as_view(), name='update-user-profile'),
    path('user/notification/', UserNotificationAPIView.as_view(), name='user-notification'),
    path('user/change-password/', UserChangePasswordAPIView.as_view(), name='change-password'),
    
  
    path('static-content',ApiViewOnboard.as_view(),name='static-content'),
    path('about-us',ApiViewAboutUs.as_view(),name='about-us'),
    
    
    path('user-interests/', UserIntrestModelAPIView.as_view(), name='user_interests_list'),
    path('user-interests/<int:pk>/', UserIntrestModelDetailAPIView.as_view(), name='user_interest_detail'),

    path('feedbacks/', UserFeedbackAPIView.as_view()),
    path('feedbacks/<int:pk>', UserFeedbackDetailAPIView.as_view()),
]+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.contrib import admin
from .models import *

admin.site.register(MyUser)
admin.site.register(InterestModel)

admin.site.register(GoalModel)
admin.site.register(GoalImagesModel)

admin.site.register(TaskModel)

admin.site.register(DairyModel)
admin.site.register(DairyImagesModel)


admin.site.register(VisionModel)
admin.site.register(VisionImagesModel)

admin.site.register(StaticManagement)

admin.site.register(AchievementModel)

admin.site.register(RewardModel)
admin.site.register(UserAchievementRewardModel)
admin.site.register(UserDeviceTokenModel)
admin.site.register(UserIntrestModel)


admin.site.register(OnBoardModel)
admin.site.register(AboutAsmodel)


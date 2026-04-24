from django.contrib import admin
from .models import DailyReview, MistakeTag, PositionCheckpoint, PreTradePlan, SetupSnapshot, SetupTag, TradeJournal, TradeReview

admin.site.register(SetupTag)
admin.site.register(MistakeTag)
admin.site.register(DailyReview)
admin.site.register(TradeJournal)
admin.site.register(TradeReview)
admin.site.register(PositionCheckpoint)
admin.site.register(PreTradePlan)
admin.site.register(SetupSnapshot)

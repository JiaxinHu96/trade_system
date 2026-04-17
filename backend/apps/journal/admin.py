from django.contrib import admin
from .models import SetupTag, MistakeTag, DailyReview, TradeJournal

admin.site.register(SetupTag)
admin.site.register(MistakeTag)
admin.site.register(DailyReview)
admin.site.register(TradeJournal)

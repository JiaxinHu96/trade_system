from django.contrib import admin
from .models import RawIBKRExecution, TradeFill, TradeGroup, TradeLotSnapshot

admin.site.register(RawIBKRExecution)
admin.site.register(TradeFill)
admin.site.register(TradeGroup)
admin.site.register(TradeLotSnapshot)

from django.db import models
from django.utils import timezone


class SetupTag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=32, default='blue')

    def __str__(self):
        return self.name


class MistakeTag(models.Model):
    name = models.CharField(max_length=64, unique=True)
    color = models.CharField(max_length=32, default='red')

    def __str__(self):
        return self.name


class DailyReview(models.Model):
    review_date = models.DateField(default=timezone.localdate, db_index=True)
    market_summary = models.TextField(blank=True, default='')
    emotions = models.TextField(blank=True, default='')
    lessons = models.TextField(blank=True, default='')
    next_day_plan = models.TextField(blank=True, default='')
    image_url = models.CharField(max_length=500, blank=True, default='')
    related_trade_group = models.ForeignKey(
        'trades.TradeGroup',
        on_delete=models.SET_NULL,
        related_name='daily_reviews',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-review_date', '-updated_at']


class DailyReviewImage(models.Model):
    daily_review = models.ForeignKey(DailyReview, on_delete=models.CASCADE, related_name='images')
    image_url = models.CharField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sort_order', 'id']


class TradeJournal(models.Model):
    trade_group = models.OneToOneField('trades.TradeGroup', on_delete=models.CASCADE, related_name='journal')
    thesis = models.TextField(blank=True, default='')
    execution_notes = models.TextField(blank=True, default='')
    exit_notes = models.TextField(blank=True, default='')
    rating = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

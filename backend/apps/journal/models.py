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
    strategy = models.CharField(max_length=128, blank=True, default='')
    market_summary = models.TextField(blank=True, default='')
    emotions = models.TextField(blank=True, default='')
    thesis = models.TextField(blank=True, default='')
    entry_logic = models.TextField(blank=True, default='')
    exit_logic = models.TextField(blank=True, default='')
    lessons = models.TextField(blank=True, default='')
    next_day_plan = models.TextField(blank=True, default='')
    image_url = models.CharField(max_length=500, blank=True, default='')
    market_regime = models.CharField(max_length=64, blank=True, default='')
    key_levels_catalyst = models.TextField(blank=True, default='')
    watchlist = models.TextField(blank=True, default='')
    daily_bias = models.CharField(max_length=128, blank=True, default='')
    max_daily_loss_respected = models.BooleanField(null=True, blank=True)
    discipline_score = models.PositiveSmallIntegerField(null=True, blank=True)
    emotional_control_score = models.PositiveSmallIntegerField(null=True, blank=True)
    biggest_mistake = models.TextField(blank=True, default='')
    session = models.CharField(max_length=32, blank=True, default='')
    market_condition = models.CharField(max_length=32, blank=True, default='')
    confidence_score = models.PositiveSmallIntegerField(null=True, blank=True)
    rule_followed = models.BooleanField(null=True, blank=True)
    trade_quality_grade = models.CharField(max_length=4, blank=True, default='')
    would_take_again = models.BooleanField(null=True, blank=True)
    related_trade_group = models.ForeignKey(
        'trades.TradeGroup',
        on_delete=models.SET_NULL,
        related_name='daily_reviews',
        null=True,
        blank=True,
    )
    mistake_tags = models.ManyToManyField('MistakeTag', blank=True, related_name='daily_reviews')
    related_trade_groups = models.ManyToManyField(
        'trades.TradeGroup',
        related_name='daily_review_links',
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


class TradeReview(models.Model):
    GRADE_CHOICES = [
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
        ('D', 'D'),
    ]

    trade_group = models.OneToOneField('trades.TradeGroup', on_delete=models.CASCADE, related_name='trade_review')
    daily_review = models.ForeignKey(
        DailyReview,
        on_delete=models.SET_NULL,
        related_name='trade_reviews',
        null=True,
        blank=True,
    )
    strategy = models.CharField(max_length=128, blank=True, default='')
    setup = models.ForeignKey(SetupTag, on_delete=models.SET_NULL, null=True, blank=True, related_name='trade_reviews')
    session = models.CharField(max_length=32, blank=True, default='')
    thesis = models.TextField(blank=True, default='')
    entry_trigger = models.TextField(blank=True, default='')
    invalidation = models.TextField(blank=True, default='')
    planned_target = models.TextField(blank=True, default='')
    sizing_rationale = models.TextField(blank=True, default='')
    entry_quality = models.PositiveSmallIntegerField(null=True, blank=True)
    exit_quality = models.PositiveSmallIntegerField(null=True, blank=True)
    risk_management = models.PositiveSmallIntegerField(null=True, blank=True)
    followed_plan = models.BooleanField(null=True, blank=True)
    would_take_again = models.CharField(max_length=32, blank=True, default='')
    mistake_tags = models.ManyToManyField(MistakeTag, blank=True, related_name='trade_reviews')
    emotion_before = models.CharField(max_length=64, blank=True, default='')
    emotion_during = models.CharField(max_length=64, blank=True, default='')
    emotion_after = models.CharField(max_length=64, blank=True, default='')
    what_i_did_well = models.TextField(blank=True, default='')
    what_to_improve = models.TextField(blank=True, default='')
    realized_r = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    final_grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True, default='')
    screenshots = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at', '-id']


class PositionCheckpoint(models.Model):
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('reduced', 'Reduced'),
        ('closed', 'Closed'),
    ]

    trade_group = models.ForeignKey('trades.TradeGroup', on_delete=models.CASCADE, related_name='position_checkpoints')
    review_date = models.DateField(default=timezone.localdate, db_index=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='open')
    carry_reason = models.TextField(blank=True, default='')
    gap_risk_note = models.TextField(blank=True, default='')
    thesis_update = models.TextField(blank=True, default='')
    next_session_plan = models.TextField(blank=True, default='')
    exit_condition_unchanged = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-review_date', '-updated_at']

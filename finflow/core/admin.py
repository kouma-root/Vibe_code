from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.db.models import Sum
from .models import User, Portfolio, Investment, Transaction


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom User admin with additional fields for financial profile.
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 
                   'risk_tolerance', 'investment_style', 'is_staff', 'date_joined')
    list_filter = ('risk_tolerance', 'investment_style', 'is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Financial Profile', {
            'fields': ('risk_tolerance', 'investment_style')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Financial Profile', {
            'fields': ('risk_tolerance', 'investment_style')
        }),
    )


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    """
    Portfolio admin with user-friendly display and filtering.
    """
    list_display = ('name', 'user', 'is_active', 'created_at', 'age_days')
    list_filter = ('is_active', 'created_at', 'user__risk_tolerance', 'user__investment_style')
    search_fields = ('name', 'description', 'user__username', 'user__email')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'age_days')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'description')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'age_days'),
            'classes': ('collapse',)
        }),
    )
    
    def age_days(self, obj):
        """Display portfolio age in days."""
        return obj.age_days
    age_days.short_description = 'Age (days)'


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    """
    Investment admin with financial calculations and filtering.
    """
    list_display = ('symbol', 'portfolio', 'quantity', 'purchase_price', 'total_value', 'days_held', 'purchase_date')
    list_filter = ('symbol', 'portfolio__user', 'portfolio', 'purchase_date')
    search_fields = ('symbol', 'portfolio__name', 'portfolio__user__username')
    ordering = ('-purchase_date',)
    readonly_fields = ('created_at', 'updated_at', 'total_value', 'days_held')
    
    fieldsets = (
        ('Investment Details', {
            'fields': ('portfolio', 'symbol', 'quantity', 'purchase_price', 'purchase_date')
        }),
        ('Calculated Values', {
            'fields': ('total_value', 'days_held'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def total_value(self, obj):
        """Display total value of the investment."""
        return f"${obj.total_value:,.2f}"
    total_value.short_description = 'Total Value'
    
    def days_held(self, obj):
        """Display days held."""
        return f"{obj.days_held} days"
    days_held.short_description = 'Days Held'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """
    Transaction admin with investment details and filtering.
    """
    list_display = ('investment', 'transaction_type', 'amount', 'timestamp', 'is_buy', 'is_sell')
    list_filter = ('transaction_type', 'timestamp', 'investment__portfolio', 'investment__symbol')
    search_fields = ('investment__symbol', 'investment__portfolio__name', 'notes')
    ordering = ('-timestamp',)
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('investment', 'transaction_type', 'amount', 'notes')
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )
    
    def is_buy(self, obj):
        """Display if this is a buy transaction."""
        if obj.is_buy:
            return format_html('<span style="color: green;">✓ Buy</span>')
        return format_html('<span style="color: red;">✗ Not Buy</span>')
    is_buy.short_description = 'Is Buy'
    
    def is_sell(self, obj):
        """Display if this is a sell transaction."""
        if obj.is_sell:
            return format_html('<span style="color: red;">✓ Sell</span>')
        return format_html('<span style="color: green;">✗ Not Sell</span>')
    is_sell.short_description = 'Is Sell'


# Inline admin for Portfolio to show investments
class InvestmentInline(admin.TabularInline):
    model = Investment
    extra = 0
    readonly_fields = ('total_value', 'days_held')
    fields = ('symbol', 'quantity', 'purchase_price', 'purchase_date', 'total_value', 'days_held')


# Update PortfolioAdmin to include investments inline
class PortfolioAdminWithInvestments(PortfolioAdmin):
    inlines = [InvestmentInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('investments')


# Re-register Portfolio with investments inline
admin.site.unregister(Portfolio)
admin.site.register(Portfolio, PortfolioAdminWithInvestments)

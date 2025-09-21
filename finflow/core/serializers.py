from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Portfolio, Investment, Transaction

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for User model with financial profile fields.
    """
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'risk_tolerance', 'investment_style', 'is_active', 'date_joined',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'date_joined', 'created_at', 'updated_at']
    
    def to_representation(self, instance):
        """Add human-readable choices to the representation."""
        data = super().to_representation(instance)
        data['risk_tolerance_display'] = instance.get_risk_tolerance_display()
        data['investment_style_display'] = instance.get_investment_style_display()
        return data


class UserCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new users.
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password', 'password_confirm',
            'risk_tolerance', 'investment_style'
        ]
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        """Create user with hashed password."""
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class TransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Transaction model.
    """
    is_buy = serializers.ReadOnlyField()
    is_sell = serializers.ReadOnlyField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'investment', 'transaction_type', 'amount', 'timestamp', 'notes',
            'is_buy', 'is_sell'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def to_representation(self, instance):
        """Add human-readable transaction type."""
        data = super().to_representation(instance)
        data['transaction_type_display'] = instance.get_transaction_type_display()
        return data


class InvestmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Investment model with calculated fields.
    """
    total_value = serializers.ReadOnlyField()
    days_held = serializers.ReadOnlyField()
    transactions = TransactionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Investment
        fields = [
            'id', 'portfolio', 'symbol', 'quantity', 'purchase_price', 'purchase_date',
            'total_value', 'days_held', 'transactions', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_symbol(self, value):
        """Validate symbol format."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Symbol cannot be empty.")
        return value.strip().upper()
    
    def validate_quantity(self, value):
        """Validate quantity is positive."""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive.")
        return value
    
    def validate_purchase_price(self, value):
        """Validate purchase price is positive."""
        if value <= 0:
            raise serializers.ValidationError("Purchase price must be positive.")
        return value


class InvestmentCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating investments.
    """
    class Meta:
        model = Investment
        fields = ['symbol', 'quantity', 'purchase_price', 'purchase_date']
    
    def validate_symbol(self, value):
        """Validate symbol format."""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Symbol cannot be empty.")
        return value.strip().upper()


class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for Portfolio model with nested investments.
    """
    age_days = serializers.ReadOnlyField()
    investments = InvestmentSerializer(many=True, read_only=True)
    investment_count = serializers.SerializerMethodField()
    total_invested = serializers.SerializerMethodField()
    
    class Meta:
        model = Portfolio
        fields = [
            'id', 'user', 'name', 'description', 'is_active', 'created_at', 'updated_at',
            'age_days', 'investments', 'investment_count', 'total_invested'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']
    
    def get_investment_count(self, obj):
        """Get count of investments in this portfolio."""
        return obj.investments.count()
    
    def get_total_invested(self, obj):
        """Get total amount invested in this portfolio."""
        from django.db.models import Sum, F
        total = obj.investments.aggregate(
            total=Sum(F('quantity') * F('purchase_price'))
        )['total']
        return total or 0


class PortfolioCreateSerializer(serializers.ModelSerializer):
    """
    Simplified serializer for creating portfolios.
    """
    class Meta:
        model = Portfolio
        fields = ['name', 'description', 'is_active']
    
    def create(self, validated_data):
        """Create portfolio for the current user."""
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class PortfolioUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating portfolios.
    """
    class Meta:
        model = Portfolio
        fields = ['name', 'description', 'is_active']
    
    def validate_name(self, value):
        """Validate portfolio name is unique for the user."""
        user = self.context['request'].user
        if self.instance:
            # Update case - check if name conflicts with other portfolios
            if Portfolio.objects.filter(user=user, name=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("A portfolio with this name already exists.")
        else:
            # Create case - check if name already exists
            if Portfolio.objects.filter(user=user, name=value).exists():
                raise serializers.ValidationError("A portfolio with this name already exists.")
        return value


class PortfolioDetailSerializer(PortfolioSerializer):
    """
    Detailed serializer for portfolio with full investment and transaction data.
    """
    investments = InvestmentSerializer(many=True, read_only=True)
    
    class Meta(PortfolioSerializer.Meta):
        fields = PortfolioSerializer.Meta.fields + ['user_details']
    
    def to_representation(self, instance):
        """Add user details to the representation."""
        data = super().to_representation(instance)
        data['user_details'] = {
            'username': instance.user.username,
            'full_name': instance.user.full_name,
            'risk_tolerance': instance.user.get_risk_tolerance_display(),
            'investment_style': instance.user.get_investment_style_display()
        }
        return data

# api/serializers.py

from rest_framework import serializers
from .models import Video, VideoLike # <-- ДОБАВЛЕНО: Импортируем VideoLike
from .models import Comment
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# --- Определите требуемый код доступа ---
# Для простоты примера, хардкодим его здесь.
# В реальном приложении лучше хранить его в settings.py и импортировать:
# from django.conf import settings
# REQUIRED_ACCESS_CODE = settings.REGISTRATION_ACCESS_CODE
REQUIRED_ACCESS_CODE = "admin"


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class VideoSerializer(serializers.ModelSerializer):
    # Поле username автора только для чтения
    author_username = serializers.ReadOnlyField(source='author.username')
    # Поле для получения полного URL файла видео
    file_url = serializers.SerializerMethodField()
    # <-- НОВОЕ: Поле для проверки, лайкнул ли текущий пользователь видео
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = [
            'id',
            'title',
            'description',
            'video', 
            'file_url', # Поле для полного URL файла видео (SerializerMethodField)
            'author', # Поле автора (ForeignKey)
            'author_username', # Поле username автора (ReadOnlyField)
            'uploaded_at',
            'thumbnail', # Поле миниатюры
            'views_count', # Поле для счетчика просмотров
            'likes_count', # <-- ДОБАВЛЕНО: Поле для счетчика лайков
            'is_liked'     # <-- ДОБАВЛЕНО: Поле, показывающее, лайкнул ли пользователь
        ]
        # Поля, которые не могут быть изменены при создании/обновлении через этот сериализатор
        read_only_fields = ['author', 'uploaded_at', 'thumbnail', 'views_count', 'likes_count'] 
        # Если у вас есть другие read_only поля, добавьте их сюда

    # Метод для получения полного URL файла видео
    def get_file_url(self, obj):
        request = self.context.get('request')
        # Проверяем наличие файла и объекта запроса
        if obj.video and request:
            # Возвращаем полный URL файла видео
            return request.build_absolute_uri(obj.video.url)
        # Если файла нет или нет объекта запроса, возвращаем None
        return None

    # <-- НОВЫЙ МЕТОД: Для определения, лайкнул ли текущий пользователь видео
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return VideoLike.objects.filter(video=obj, user=request.user).exists()
        return False
    # --- КОНЕЦ НОВОГО МЕТОДА ---

    # Переопределяем метод create для автоматического назначения автора
    def create(self, validated_data):
        # Устанавливаем текущего пользователя как автора видео
        validated_data['author'] = self.context['request'].user
        # Вызываем стандартный метод create для сохранения объекта
        return super().create(validated_data)

# Сериализатор для регистрации пользователя
class RegistrationSerializer(serializers.ModelSerializer):
    # Поле для пароля (только для записи, обязательное, с валидаторами)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        validators=[validate_password] # Используем стандартные валидаторы Django для пароля
    )
    # Поле для подтверждения пароля (только для записи, обязательное)
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        required=True
    )

    access_code = serializers.CharField(
        write_only=True, # Поле только для записи (не будет в ответе API)
        required=True    # Поле обязательно для регистрации
    )


    class Meta:
        model = User
        # --- ДОБАВЛЕНО: Включаем access_code в список полей ---
        fields = ('username', 'email', 'password', 'password2', 'access_code')
        # --- Конец добавления поля ---
        # Убеждаемся, что email обязателен
        extra_kwargs = {
            'email': {'required': True}
        }

    # Метод для дополнительной валидации (сравнение паролей, проверка email, проверка кода доступа)
    def validate(self, attrs):
        # Проверяем совпадение паролей
        if attrs.get('password') != attrs.get('password2'):
            # Используем serializers.ValidationError для правильной обработки DRF
            raise serializers.ValidationError({"password": "Пароли не совпадают"})

        # Проверяем, не занят ли email
        if User.objects.filter(email=attrs.get('email')).exists():
             # Используем serializers.ValidationError
             raise serializers.ValidationError({"email": "Этот email уже используется"})

        provided_code = attrs.get('access_code')

        # Проверяем, был ли код предоставлен и совпадает ли он с требуемым
        if not provided_code or provided_code != REQUIRED_ACCESS_CODE:
            # Возвращаем ошибку валидации для поля access_code
            raise serializers.ValidationError({"access_code": "Неверный или отсутствует код доступа."})
        
        return attrs # Возвращаем валидированные данные

    # определяем метод create для создания пользователя
    def create(self, validated_data):
    
        validated_data.pop('password2', None)
        validated_data.pop('access_code', None) 
    
        # Создаем пользователя с помощью create_user (автоматически хэширует пароль)
        user = User.objects.create_user(**validated_data)
        return user

class CommentSerializer(serializers.ModelSerializer):
    # Это поле будет содержать ТОЛЬКО строку с именем пользователя
    author = serializers.ReadOnlyField(source='author.username')

    class Meta:
        model = Comment
        fields = ['id', 'video', 'author', 'text', 'created_at']
        read_only_fields = ['id', 'video', 'author', 'created_at']
# twix/api/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import generics, permissions

# <-- ДОБАВЛЕНО: Импортируем VideoLike
from .models import Video, Comment, VideoLike 
from .serializers import VideoSerializer, RegistrationSerializer, UserSerializer, CommentSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly, AllowAny, IsAuthenticated

from django.contrib.auth.models import User
from .permissions import IsVideoOwner

from django.core.files import File
import os
from django.conf import settings
import sys

# ДОБАВЛЕНО: Для F() выражений
from django.db.models import F
# ДОБАВЛЕНО: Для IntegrityError при уникальных ограничениях
from django.db import IntegrityError 

# --- НОВАЯ СТРОКА: Импортируем 'models' из django.db ---
from django.db import models # <-- ЭТА СТРОКА УЖЕ БЫЛА ДОБАВЛЕНА РАНЕЕ

# ДОБАВЛЕНО: Для Case, When, PositiveIntegerField (они также из django.db.models)
from django.db.models import Case, When, PositiveIntegerField 


MOVIEPY_INSTALLED = False

print("\n--- Debugging moviepy import ---")
print(f"sys.executable: {sys.executable}")
print(f"sys.path: {sys.path}")
print("Attempting to import moviepy.editor...")

try:
    from moviepy import VideoFileClip
    MOVIEPY_INSTALLED = True
    print("moviepy.editor imported successfully!")
    print("Thumbnail generation is enabled.")
except ImportError as e:
    print(f"Error importing moviepy.editor: {e}")
    print("Warning: moviepy not installed or not found in sys.path. Thumbnail generation will be skipped.")
    print("Please ensure moviepy is installed (pip install moviepy) in the correct environment.")
except Exception as e:
    print(f"An unexpected error occurred during moviepy import: {type(e).__name__}: {e}")
    print("Warning: moviepy import failed. Thumbnail generation will be skipped.")
    print("Please ensure moviepy is installed and ffmpeg is in your system's PATH.")

print("--- End debugging moviepy import ---\n")

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

class UserVideoListView(generics.ListAPIView):
    serializer_class = VideoSerializer

    def get_queryset(self):
        return Video.objects.filter(author=self.request.user)


class VideoViewSet(viewsets.ModelViewSet):
    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def get_permissions(self):
        if self.action == 'list' or self.action == 'retrieve':
            permission_classes = [permissions.AllowAny]
        elif self.action == 'create':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'destroy':
            permission_classes = [permissions.IsAuthenticated, IsVideoOwner]
        elif self.action == 'update' or self.action == 'partial_update':
            permission_classes = [permissions.IsAuthenticated, IsVideoOwner]
        elif self.action == 'user':
            permission_classes = [permissions.IsAuthenticated]
        elif self.action == 'increment_view' or self.action == 'like_toggle':
            permission_classes = [permissions.AllowAny]
            if self.action == 'like_toggle':
                permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [permissions.IsAuthenticated]

        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        instance = serializer.save(author=self.request.user)

        if MOVIEPY_INSTALLED and instance.video:
            print(f"Attempting to generate thumbnail for video {instance.pk}...")
            try:
                video_path = instance.video.path
                temp_thumbnail_path = os.path.join(settings.MEDIA_ROOT, f'temp_thumbnail_{instance.pk}.jpg')

                clip = VideoFileClip(video_path)

                frame_time = 0.5
                if clip.duration is not None and clip.duration > 0:
                    frame_time = min(frame_time, clip.duration / 2)
                else:
                    print(f"Warning: Video {instance.pk} has zero or unknown duration. Skipping thumbnail generation.")
                    clip.close()
                    return

                clip.save_frame(temp_thumbnail_path, t=frame_time)
                clip.close()

                with open(temp_thumbnail_path, 'rb') as f:
                    thumbnail_filename = f'thumbnail_{instance.pk}_{os.path.splitext(os.path.basename(video_path))[0]}.jpg'
                    instance.thumbnail.save(thumbnail_filename, File(f), save=True)
                    print(f"Thumbnail generated and saved for video {instance.pk}.")

                os.remove(temp_thumbnail_path)
                print(f"Temporary thumbnail file {temp_thumbnail_path} removed.")

            except Exception as e:
                print(f"Error generating thumbnail for video {instance.pk}: {e}")
                instance.thumbnail = None
                instance.save(update_fields=['thumbnail'])

        elif not MOVIEPY_INSTALLED:
            print(f"Skipping thumbnail generation for video {instance.pk}: moviepy not installed.")
        elif not instance.video:
            print(f"Skipping thumbnail generation for video {instance.pk}: no video file.")

    @action(detail=True, methods=['post'])
    def increment_view(self, request, pk=None):
        try:
            video = self.get_object()
            
            video.views_count = F('views_count') + 1
            video.save(update_fields=['views_count']) 
            
            video.refresh_from_db()

            print(f"Video {pk} view incremented by 1. Total: {video.views_count}")
            return Response({'views_count': video.views_count}, status=status.HTTP_200_OK)
        except Video.DoesNotExist:
            return Response({'detail': 'Видео не найдено.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(f"Error incrementing view for video {pk}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def like_toggle(self, request, pk=None):
        try:
            video = self.get_object()
            user = request.user

            video_like, created = VideoLike.objects.get_or_create(video=video, user=user)

            if created:
                # Если лайк только что создан (пользователь лайкнул)
                video.likes_count = F('likes_count') + 1
                video.save(update_fields=['likes_count'])
                video.refresh_from_db() # Получаем актуальное значение
                status_code = status.HTTP_201_CREATED
                message = "Видео лайкнуто."
                is_liked = True
                print(f"User {user.username} liked video {video.pk}. Total likes: {video.likes_count}")
            else:
                # Если лайк уже существовал (пользователь дизлайкнул)
                video_like.delete() # Удаляем запись о лайке
                
                # ИСПРАВЛЕНИЕ: Используем Case для атомарного уменьшения
                # и предотвращения отрицательных значений в одной операции.
                # Если likes_count > 0, уменьшаем на 1, иначе оставляем 0.
                video.likes_count = Case(
                    When(likes_count__gt=0, then=F('likes_count') - 1),
                    default=0,
                    output_field=models.PositiveIntegerField()
                )
                video.save(update_fields=['likes_count'])
                video.refresh_from_db() # Получаем актуальное значение
                status_code = status.HTTP_200_OK
                message = "Лайк отменен."
                is_liked = False
                print(f"User {user.username} unliked video {video.pk}. Total likes: {video.likes_count}")
            
            # Возвращаем актуальное количество лайков и статус лайка для фронтенда
            return Response({
                'likes_count': video.likes_count,
                'is_liked': is_liked,
                'message': message
            }, status=status_code)

        except Video.DoesNotExist:
            return Response({'detail': 'Видео не найдено.'}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            # Очень маловероятно из-за get_or_create, но на всякий случай
            return Response({'detail': 'Ошибка целостности данных.'}, status=status.HTTP_409_CONFLICT)
        except Exception as e:
            print(f"Error toggling like for video {pk}: {e}")
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RegistrationAPIView(generics.GenericAPIView):
    serializer_class = RegistrationSerializer
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "user": RegistrationSerializer(user, context=self.get_serializer_context()).data,
            "message": "Пользователь успешно зарегистрирован.",
        }, status=status.HTTP_201_CREATED)

class VideoCommentsListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        video_id = self.kwargs['video_id']
        video = Video.objects.filter(pk=video_id).first()
        if video:
            return Comment.objects.filter(video=video)
        return Comment.objects.none()

    def perform_create(self, serializer):
        video_id = self.kwargs['video_id']
        video = Video.objects.get(pk=video_id)
        serializer.save(video=video, author=self.request.user)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated()]
        return [AllowAny()]
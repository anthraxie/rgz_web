# twix/api/models.py

from django.db import models
from django.contrib.auth.models import User

class Video(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    video = models.FileField(upload_to='videos/')
    thumbnail = models.ImageField(upload_to='thumbnails/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    views_count = models.PositiveIntegerField(default=0) # Счетчик просмотров
    likes_count = models.PositiveIntegerField(default=0) # <-- НОВОЕ: Счетчик лайков

    def __str__(self):
        return self.title

class Comment(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at'] # От самого нового к старому

    def __str__(self):
        return f"Comment by {self.author.username} on {self.video.title}"

# --- НОВАЯ МОДЕЛЬ: VideoLike ---
class VideoLike(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='likes_set') # Изменил related_name, чтобы избежать конфликта с likes_count
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Это гарантирует, что один пользователь может лайкнуть одно видео только один раз.
        unique_together = ('video', 'user')

    def __str__(self):
        return f"User {self.user.username} liked video {self.video.id}"
# --- КОНЕЦ НОВОЙ МОДЕЛИ ---
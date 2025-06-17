from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from django.db.models.signals import post_save
from django.dispatch import receiver

class Department(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_departments')
    
    def __str__(self):
        return self.name

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_important = models.BooleanField(default=False)
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('announcement_detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['-is_important', '-created_at']

class AnnouncementComment(models.Model):
    announcement = models.ForeignKey(Announcement, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_at']

class FileVersion(models.Model):
    file = models.ForeignKey('SharedFile', on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    file_content = models.FileField(upload_to='files/versions/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(default=timezone.now)
    change_notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-version_number']
        unique_together = ['file', 'version_number']

## PREVIEW
class Document(models.Model):
    file = models.FileField(upload_to='files/')
    file_type = models.CharField(max_length=10, blank=True)

    def save(self, *args, **kwargs):
        self.file_type = self.file.name.split('.')[-1].lower()
        super().save(*args, **kwargs)

class SharedFile(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to='files/')
    current_version = models.PositiveIntegerField(default=1)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    departments = models.ManyToManyField(Department)
    uploaded_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def extension(self):
        return self.file.name.split('.')[-1].lower()
    
    def save_new_version(self, new_file, user, notes=""):
        self.file = new_file
        self.current_version += 1
        self.save()
        FileVersion.objects.create(
            file=self,
            version_number=self.current_version,
            file_content=new_file,
            uploaded_by=user,
            change_notes=notes
        )
    
    class Meta:
        ordering = ['-updated_at']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True)
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=100, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.department}"
    
    def is_department_admin(self):
        return self.department and self.department.admin == self.user

class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('LOGIN', 'User login'),
        ('LOGOUT', 'User logout'),
        ('CREATE_ANN', 'Announcement created'),
        ('EDIT_ANN', 'Announcement edited'),
        ('DELETE_ANN', 'Announcement deleted'),
        ('UPLOAD_FILE', 'File uploaded'),
        ('UPDATE_FILE', 'File updated'),
        ('DELETE_FILE', 'File deleted'),
        ('ADD_COMMENT', 'Comment added'),
        ('DELETE_COMMENT', 'Comment deleted'),
        ('SEARCH', 'Search performed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=200, choices=ACTION_CHOICES)
    target = models.CharField(max_length=200, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'Activity Logs'

    def __str__(self):
        return f"{self.get_action_display()} by {self.user} at {self.timestamp}"
    
    @classmethod
    def log_action(cls, request=None, user=None, action="", target="", details="", ip_address=None):
        # Get user from request if available
        try:
            user_obj = user
            ip_addr = ip_address
        
            if request is not None:
                user_obj = request.user if hasattr(request, 'user') and request.user.is_authenticated else None
                ip_addr = request.META.get('REMOTE_ADDR', '') if hasattr(request, 'META') else None
        
            log_entry = cls(
                user=user_obj,
                action=action,
                target=str(target)[:200],
                details=str(details)[:500],
            )

            if hasattr(cls, 'ip_address'):
                log_entry.ip_address = ip_addr

            log_entry.save()
            return log_entry

        except Exception as e:
            log_entry = cls.objects.create(
                user=user_obj,
                action=action,
                target=str(target)[:200],
                details=str(details)[:500],
            )
            return log_entry

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        default_dept = Department.objects.first()  # Get first department or create one
        if not default_dept:
            default_dept = Department.objects.create(name="General", description="Default department")
        UserProfile.objects.create(user=instance, department=default_dept)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()
    else:
        default_dept = Department.objects.first()
        UserProfile.objects.create(user=instance, department=default_dept)


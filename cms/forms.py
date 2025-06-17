from django import forms
from .models import Announcement, SharedFile, Department, UserProfile, AnnouncementComment, FileVersion
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import User

class AnnouncementForm(forms.ModelForm):
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'departments', 'is_important']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
        }

class SharedFileForm(forms.ModelForm):
    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    
    class Meta:
        model = SharedFile
        fields = ['title', 'description', 'file', 'departments']
        widgets = {
                'description': forms.Textarea(attrs={'rows': 3}),
                'departments': forms.CheckboxSelectMultiple(),
                }

class FileVersionForm(forms.ModelForm):
    class Meta:
        model = FileVersion
        fields = ['file_content', 'change_notes']
        widgets = {
            'change_notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'What changed in this version?'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file_content'].label = "New File Version"
        self.fields['file_content'].required = True
        self.fields['change_notes'].required = True 

class CommentForm(forms.ModelForm):
    class Meta:
        model = AnnouncementComment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Add your comment...'}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    department = forms.ModelChoiceField(queryset=Department.objects.all())
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(user=user, department=self.cleaned_data['department'])
            ActivityLog.log_action(user, 'REGISTER', f"New user: {user.username}")
        return user

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['department', 'avatar', 'phone', 'position']

class UserEditForm(UserChangeForm):
    password = None  # Remove password field
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class SearchForm(forms.Form):
    query = forms.CharField(label='Search', max_length=100, required=False)
    search_in = forms.MultipleChoiceField(
        label='Search in',
        choices=[
            ('announcements', 'Announcements'),
            ('files', 'Files'),
            ('comments', 'Comments'),
        ],
        widget=forms.CheckboxSelectMultiple,
        initial=['announcements', 'files']
    )
    department = forms.ModelChoiceField(
        queryset=Department.objects.all(),
        required=False,
        label='Filter by department'
    )

import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, authenticate
from django.views.decorators.http import require_POST
from django.http import JsonResponse, FileResponse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import UpdateView
from django.db.models import Q
from .models import (Announcement, SharedFile, Department, UserProfile, 
                    AnnouncementComment, FileVersion, ActivityLog, Document)
from .forms import (AnnouncementForm, SharedFileForm, UserRegistrationForm,
                   CommentForm, FileVersionForm, UserProfileForm, UserEditForm,
                   SearchForm)
from django.contrib import messages
from django.core.paginator import Paginator
from django.urls import reverse_lazy
from pdf2image import convert_from_path
from tempfile import NamedTemporaryFile

@login_required
def dashboard(request):
    #get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user,
        defaults={'department': Department.objects.first()}
    )
    user_dept = user_profile.department
    
    # Get announcements for user's department
    announcements = Announcement.objects.filter(departments=user_dept).order_by('-created_at')[:5]
    
    # Get files for user's department
    shared_files = SharedFile.objects.filter(departments=user_dept).order_by('-uploaded_at')[:5]
    
    context = {
        'announcements': announcements,
        'shared_files': shared_files,
        'department': user_dept,
    }
    return render(request, 'cms/dashboard.html', context)

@login_required
def edit_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            #ActivityLog.log_action(
            #    request,
            #    'CREATE_ANN',
            #    f"Announcement: {announcement.title}",
            #    f"Departments: {', '.join([d.name for d in announcement.departments.all()])}"
            #)
            return redirect('announcement_detail', pk=announcement.pk)
            message.success(request, "Announcement updated successfully")
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, 'cms/edit_announcement.html', {
        'form': form,
        'announcement': announcement
        })

@login_required
def announcement_list(request):
    user_dept = UserProfile.objects.get(user=request.user).department
    announcements = Announcement.objects.filter(departments=user_dept).order_by('-created_at')
    
    paginator = Paginator(announcements, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'cms/announcement_list.html', context)

@login_required
@require_POST
def delete_announcement(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk, author=request.user)
    announcement.delete()
    messages.success(request, "Announcement deleted successfully")
    return redirect('announcement_list')

@login_required
def announcement_detail(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    return render(request, 'cms/announcement_detail.html', {'announcement': announcement})

@require_POST
@login_required
def increment_announcement_views(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.views += 1
    announcement.save()
    return JsanResponse({'views': announcement.views})

@login_required
def create_announcement(request):
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.author = request.user
            announcement.save()
            form.save_m2m()  # Save many-to-many relationships
            #messages.success(request, 'Announcement created successfully!')
            return redirect('announcement_detail', pk=announcement.pk)
    else:
        form = AnnouncementForm()
    return render(request, 'cms/announcement_form.html', {'form': form})

@login_required
def file_list(request):
    user_dept = request.user.userprofile.department
    files = SharedFile.objects.filter(departments=user_dept).order_by('-uploaded_at')
   
    # Search functionality
    search_query = request.GET.get('q', '')
    if search_query:
        files = files.filter(
            Q(title__icontains=search_query)  |
            Q(description__icontains=search_qurey) |
            Q(uploaded_by__first_name__icontains=search_query) |
            Q(uploaded_by__last_name__icontains=search_query)
        )
    #Department filter
    dept_filter = request.GET.get('dept', '')
    if dept_filter:
        files = files.filter(departments__id=dept_filter)

    paginator = Paginator(files, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'cms/file_list.html', {
        'page_obj': page_obj,
        'all_departments': Department.objects.all(),
        'search_query': search_query,
    })

@login_required
def upload_file(request):
    if request.method == 'POST':
        form = SharedFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.uploaded_by = request.user
            file.save()
            form.save_m2m()  # Save many-to-many relationships
            #messages.success(request, 'File uploaded successfully!')
            return redirect('file_detail', pk=file.pk)
    else:
        form = SharedFileForm()
    return render(request, 'cms/file_form.html', {'form': form})

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'cms/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)

        if not username or not password:
            messages.error(request, "Both username and password are required")
            return render(request, 'cms/login.html')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            #ActivityLog.log_action(request, 'LOGIN', f"user {username} logged in")
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials. Please try again')
            #ActivityLog.log_action(request, 'LOGIN_FAILED', f"Failed login attempt for {username}")

    return render(request, 'cms/login.html', status=200 if request.method == 'GET' else 401)

@login_required
def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def add_comment(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        #form = CommentForm(request.POST)
        if content:
            AnnouncementComment.objects.create(
                announcement=announcement,
                author=request.user,
                content=content
            )
    return redirect('announcement_detail', pk=pk)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(AnnouncementComment, pk=comment_id)
    if comment.author == request.user or request.user.userprofile.is_department_admin:
        comment.delete()
    return redirect('announcement_detail', pk=comment.announcement.pk)

@login_required
def update_file(request, pk):
    file = get_object_or_404(SharedFile, pk=pk)
    if not request.user == file.uploaded_by and not request.user.userprofile.is_department_admin:
        raise PermissionDenied

    if request.method == 'POST':
        form = FileVersionForm(request.POST, request.FILES)
        if form.is_valid():
            file.save_new_version(
                form.cleaned_data['file_content'],
                request.user,
                form.cleaned_data.get('change_notes', '')
            )
            messages.success(request, "New version uploaded successfully")
            return redirect('file_detail', pk=file.pk)
    else:
        form = FileVersionForm()

    return render(request, 'cms/file_update.html', {
        'form': form, 
        'file': file
    })


@login_required
def file_detail(request, pk):
    file = get_object_or_404(SharedFile, pk=pk)
    versions = file.versions.all()
    return render(request, 'cms/file_detail.html', {'file': file, 'versions': versions})

@login_required
@require_POST
def delete_file(request, pk):
    file = get_object_or_404(SharedFile, pk=pk)
    
    # Check permissions (owner or department admin)
    if not (request.user == file.uploaded_by or request.user.userprofile.is_department_admin):
        raise PermissionDenied
    # Log the deletion before doing it
    ActivityLog.log_action(
        request=request,
        action='DELETE_FILE',
        target=f"File: {file.title}",
        details=f"Deleted {file.versions.count} versions"
    )
    
    file.delete()
    messages.success(request, "File and all its versions have been deleted")
    return redirect('file_list')


@login_required
#def file_download(request, pk):
#    file = get_object_or_404(SharedFile, pk=pk)
#    response = FileResponse(file.file)
#    response['Content-Disposition'] = f'attachment: filename="{file.title}.{file.extension()}"' 
#    return response
def file_download(request, pk, version=None):
    """Handle file downloads with version control"""
    file = get_object_or_404(SharedFile, pk=pk)

    # Check department access
    user_dept = request.user.userprofile.department
    if not file.departments.filter(id=user_dept.id).exists():
        return HttpResponseForbidden("You don't have permission to access this file")

    # Get the appropriate file version
    if version:
        file_version = get_object_or_404(FileVersion, file=file, version_number=version)
        file_obj = file_version.file_content
        filename = f"{file.title}_v{version}.{file.extension()}"
    else:
        file_obj = file.file
        filename = f"{file.title}.{file.extension()}"

    # Create the response
    response = FileResponse(file_obj, as_attachment=True, filename=filename)

    # Log the download activity
    #ActivityLog.log(
    #    request,
    #    'DOWNLOAD',
    #    f"File:{file.id}",
    #    f"Version:{version if version else 'current'}"
    #)

    return response

@login_required
def file_download_version(request, pk, version):
    file =  get_object_or_404(SharedFile, pk=pk)
    version = get_object_or_404(FileVersion, file=file, version_number=version)
    response = FileResponse(version.file_content)
    response['Content-Disposition'] = f'attachment; filename="{file.title}_v{version.version_number}.{file.extension()}"'
    return response

@login_required
def search(request):
    form = SearchForm(request.GET or None)
    results = []

    if form.is_valid():
        query = form.cleaned_data['query']
        search_in = form.cleaned_data['search_in']
        department = form.cleaned_data['department']

        user_profile = UserProfile.objects.get(user=request.user)
        user_dept = department if department else user_profile.department

        if query:
            if 'announcements' in search_in:
                announcements = Announcement.objects.filter(
                    Q(departments=user_dept),
                    Q(title__icontains=query) | Q(content__icontains=query)
                ).distinct()
                results.extend(announcements)

            if 'files' in search_in:
                files = SharedFile.objects.filter(
                    Q(departments=user_dept),
                    Q(title__icontains=query) | Q(description__icontains=query)
                ).distinct()
                results.extend(files)

            if 'comments' in search_in:
                comments = AnnouncementComment.objects.filter(
                    Q(announcement__departments=user_dept),
                    Q(content__icontains=query)
                ).distinct()
                results.extend(comments)

        ActivityLog.log_action(
            request.user,
            'SEARCH',
            f"Query: {query}",
            f"Filters: {search_in}"
        )

    context = {
        'form': form,
        'results': results,
        'query': request.GET.get('query', ''),
    }
    return render(request, 'cms/search.html', context)

class ProfileUpdateView(UserPassesTestMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'cms/profile_edit.html'

    def get_object(self):
        return self.request.user.userprofile

    def test_func(self):
        return self.request.user.is_authenticated

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserEditForm(instance=self.request.user)
        return context

    def form_valid(self, form):
        user_form = UserEditForm(self.request.POST, instance=self.request.user)
        if user_form.is_valid():
            user_form.save()
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, 'Profile updated successfully!')
        #ActivityLog.log_action(
        #    self.request.user,
        #    'UPDATE_PROFILE',
        #    "User updated profile"
        #)
        return reverse_lazy('profile_view', kwargs={'pk': self.request.user.pk})

@login_required
def profile_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    activities = ActivityLog.objects.filter(user=user).order_by('-timestamp')[:10]
    return render(request, 'cms/profile.html', {'profile_user': user, 'activities': activities})

@login_required
def activity_log(request):
    logs = ActivityLog.objects.all().order_by('-timestamp')

    #user_profile = UserProfile.objects.get(user=request.user)
    # Filter by action type if specified
    action_filter = request.GET.get('action')
    if action_filter:
        logs = logs.filter(action=action_filter)

    # For department admins, show only their department's activities
    if hasattr(request.user, 'userprofile') and request.user.userprofile.is_department_admin():
        user_dept = request.user.userprofile.department
        logs = logs.filter(
            Q(user__userprofile__department=user_dept) |
            Q(target__contains=str(user_dept))
        )

    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'cms/activity_log.html', {
        'page_obj': page_obj,
        'action_types': ActivityLog.ACTION_CHOICES
    
        })


def preview_file(request, file_path):
    if file_path.endswith('.pdf'):
        images = convert_from_path(file_path)
        with NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
            images[0].save(temp, format='JPEG')
            return FileResponse(open(temp.name, 'rb'), content_type='image/jpeg')

def document_preview(request, pk):
    document = get_object_or_404(Document, pk=pk)
    if document.file_type in ['pdf', 'jpg', 'jpeg', 'png', 'gif']:
        return render(request, 'preview.html', {'document': document})
    else:
        return HttpResponse("Preview not available for this file type")


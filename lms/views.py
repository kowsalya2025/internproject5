from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Prefetch
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.utils import timezone
from urllib3 import request
from .models import Instructor
from .models import HomeBanner
from .models import Testimonial, FAQ
from .models import (
    HeroSection,  
    Course, 
    CourseEnrollment,
    FeatureSection, 
    HomeAboutSection, 
    CourseCategory,  
    Payment,
    CurriculumDay,
    Video,
    Purchase,
    UserVideoProgress
)
import razorpay
import json
import uuid

# Get User model
User = get_user_model()

# Initialize Razorpay client
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


# ===== AUTHENTICATION VIEWS =====
def home(request):
    """Home page view with hero section, categories, and featured courses"""
    hero = HeroSection.objects.filter(is_active=True).first()
    feature_section = FeatureSection.objects.filter(is_active=True).first()
    about_section = HomeAboutSection.objects.filter(is_active=True).first()
    
    categories = CourseCategory.objects.filter(is_active=True).order_by('order')
    banner = HomeBanner.objects.filter(is_active=True).first() 
    instructors = Instructor.objects.all()
    testimonials = Testimonial.objects.filter(is_active=True)
    faqs = FAQ.objects.filter(is_active=True)
    
    # Try to get featured courses, fall back to regular courses
    featured_courses = Course.objects.filter(is_active=True)
    
    # Check if Course model has is_featured field
    if hasattr(Course, 'is_featured'):
        featured_courses = featured_courses.filter(is_featured=True)
    
    featured_courses = featured_courses.order_by('-created_at')[:8]
    
    if featured_courses.count() < 8:
        additional_courses = Course.objects.filter(
            is_active=True
        ).exclude(
            id__in=[c.id for c in featured_courses]
        ).order_by('-created_at')[:8 - featured_courses.count()]
        courses = list(featured_courses) + list(additional_courses)
    else:
        courses = featured_courses
    
    all_courses_count = Course.objects.filter(is_active=True).count()
    
    context = {
        'hero': hero,
        'feature_section': feature_section,
        'about_section': about_section,
        'categories': categories,
        'courses': courses,
        'all_courses_count': all_courses_count,
        'banner': banner,
        'instructors': instructors,
        'testimonials': testimonials,
        'faqs': faqs,
    }
    return render(request, 'lms/home.html', context)


def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password!')
            return redirect('login')
        
        try:
            # Find user by email
            user = User.objects.get(email=email)
            # Authenticate with username (which is email in your signup)
            auth_user = authenticate(request, username=user.username, password=password)
            
            if auth_user is not None:
                login(request, auth_user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome back, {auth_user.first_name or auth_user.username}!')
                next_url = request.GET.get('next')
                return redirect(next_url or 'home')
            else:
                messages.error(request, 'Invalid email or password!')
                return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email!')
            return redirect('login')
    
    return render(request, 'lms/login.html')


def signup_view(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not all([name, email, password, confirm_password]):
            messages.error(request, 'All fields are required!')
            return redirect('signup')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return redirect('signup')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long!')
            return redirect('signup')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered!')
            return redirect('signup')
        
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )
            # Authenticate and login the user
            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome {name}! Account created successfully!')
                return redirect('home')
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
            return redirect('signup')
    
    return render(request, 'lms/signup.html')


def logout_view(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('home')


# ===== COURSE VIEWS =====
def all_courses(request):
    """View for all courses page with filtering"""
    courses = Course.objects.filter(is_active=True).order_by('-created_at')
    categories = CourseCategory.objects.filter(is_active=True).order_by('order')
    
    category_counts = {}
    for category in categories:
        category_counts[category.slug] = Course.objects.filter(
            category=category, 
            is_active=True
        ).count()
    
    all_courses_count = courses.count()
    
    category_slug = request.GET.get('category')
    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    
    context = {
        'courses': courses,
        'categories': categories,
        'category_counts': category_counts,
        'all_courses_count': all_courses_count,
        'selected_category': category_slug,
    }
    return render(request, 'courses/all.html', context)


def courses_by_category(request, category_slug):
    """View for courses filtered by category"""
    category = get_object_or_404(CourseCategory, slug=category_slug, is_active=True)
    courses = Course.objects.filter(category=category, is_active=True).order_by('-created_at')
    all_categories = CourseCategory.objects.filter(is_active=True).order_by('order')
    
    context = {
        'category': category,
        'courses': courses,
        'categories': all_categories,
        'selected_category': category_slug,
    }
    return render(request, 'courses/category.html', context)


def course_detail(request, slug):
    """Display course detail page with curriculum"""
    course = get_object_or_404(
        Course.objects.prefetch_related(
            'instructors',
            Prefetch(
                'curriculum_days',
                queryset=CurriculumDay.objects.prefetch_related('videos').order_by('order', 'day_number')
            )
        ),
        slug=slug,
        is_active=True
    )

    # Check if user has purchased the course
    user_has_paid = False
    if request.user.is_authenticated:
        user_has_paid = Purchase.objects.filter(
            user=request.user,
            course=course,
            payment_status='completed'
        ).exists()

    # Find first accessible video for "Start Learning" button
    first_video = None
    for day in course.curriculum_days.all():
        for video in day.videos.all().order_by('order', 'id'):
            if video.is_accessible_by(request.user):
                first_video = video
                break
        if first_video:
            break

    # Prepare curriculum with video access info
    curriculum_days = []
    for day in course.curriculum_days.all():
        day_data = {
            'day_number': day.day_number,
            'title': day.title,
            'description': day.description,
            'videos': []
        }

        for video in day.videos.all().order_by('order', 'id'):
            # Centralized access check
            is_accessible = video.is_accessible_by(request.user)

            # Check completion status
            is_completed = False
            if request.user.is_authenticated:
                progress = UserVideoProgress.objects.filter(
                    user=request.user,
                    video=video
                ).first()
                if progress:
                    is_completed = progress.is_completed

            day_data['videos'].append({
                'id': video.id,
                'title': video.title,
                'description': video.description,
                'duration': video.duration,
                'is_accessible': is_accessible,
                'is_completed': is_completed
            })

        curriculum_days.append(day_data)

    context = {
        'course': course,
        'curriculum_days': curriculum_days,
        'user_has_paid': user_has_paid,
        'first_video': first_video,
        'discount_percentage': course.get_discount_percentage(),
        'skills_list': course.get_skills_list(),
        'tools_list': course.get_tools_list(),
    }

    return render(request, 'courses/detail.html', context)




@login_required
def initiate_purchase(request, slug):
    """Handle purchase initiation"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    # Check if user already purchased
    existing_purchase = Purchase.objects.filter(
        user=request.user,
        course=course,
        payment_status='completed'
    ).first()
    
    if existing_purchase:
        messages.info(request, 'You have already purchased this course.')
        return redirect('course_detail', slug=slug)
    
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        agree_terms = request.POST.get('agree_terms')
        
        if not all([full_name, email, agree_terms]):
            messages.error(request, 'Please fill all required fields and agree to terms.')
            return redirect('course_detail', slug=slug)
        
        # Create pending purchase
        purchase = Purchase.objects.create(
            user=request.user,
            course=course,
            amount_paid=course.discounted_price,
            payment_status='pending',
            full_name=full_name,
            email=email
        )
        
        # In a real application, integrate with payment gateway here
        # For now, we'll redirect to a payment page
        return redirect('payment_page', purchase_id=purchase.id)
    
    return redirect('course_detail', slug=slug)


@login_required
def payment_page(request, purchase_id):
    """Display payment page"""
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    
    if purchase.payment_status == 'completed':
        messages.info(request, 'This purchase is already completed.')
        return redirect('course_detail', slug=purchase.course.slug)
    
    context = {
        'purchase': purchase,
        'course': purchase.course
    }
    
    return render(request, 'lms/payment_page.html', context)


@login_required
@require_POST
def complete_payment(request, purchase_id):
    """Complete the payment process"""
    purchase = get_object_or_404(Purchase, id=purchase_id, user=request.user)
    
    # In real application, verify payment with gateway
    # For demo, we'll mark as completed
    transaction_id = request.POST.get('transaction_id', f'TXN{purchase.id}')
    
    purchase.payment_status = 'completed'
    purchase.transaction_id = transaction_id
    purchase.save()
    
    messages.success(request, 'Payment successful! You now have access to the full course.')
    return redirect('course_detail', slug=purchase.course.slug)



from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

@csrf_exempt
def save_video_progress(request, video_id):
    """Save video progress (for auto-save)"""
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Authentication required'}, status=401)
    
    try:
        video = Video.objects.get(id=video_id)
        data = json.loads(request.body)
        watched_percentage = data.get('watched_percentage', 0)
        
        progress, created = UserVideoProgress.objects.update_or_create(
            user=request.user,
            video=video,
            defaults={
                'watched_percentage': watched_percentage
            }
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

# lms/views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

# lms/views.py
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from .models import UserVideoProgress

@require_POST
@csrf_exempt  # Only use this for testing, remove in production or use proper CSRF handling
def mark_video_complete(request, video_id):
    """Mark a video as completed for the current user"""
    try:
        video = Video.objects.get(id=video_id)
        
        # Get or create progress record
        progress, created = UserVideoProgress.objects.get_or_create(
            user=request.user,
            video=video
        )
        
        # Mark as completed
        progress.is_completed = True
        progress.watched_percentage = 100
        progress.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Video marked as complete',
            'video_id': video_id
        })
        
    except Video.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Video not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
def my_courses(request):
    """Display user's purchased courses with improved data handling"""
    # Get purchases from new Purchase model
    purchases = Purchase.objects.filter(
        user=request.user,
        payment_status='completed'
    ).select_related('course__category').prefetch_related(
        'course__instructors',
        'course__curriculum_days__videos'
    ).order_by('-purchased_at')
    
    # Also get enrollments from CourseEnrollment (legacy)
    enrollments = CourseEnrollment.objects.filter(
        user=request.user
    ).select_related('course__category').prefetch_related(
        'course__instructors',
        'course__curriculum_days__videos'
    ).order_by('-enrolled_at')
    
    # Get list of course IDs from purchases to avoid duplicates
    purchased_course_ids = [p.course.id for p in purchases]
    
    # Filter out enrollments that are already in purchases
    enrollments = [e for e in enrollments if e.course.id not in purchased_course_ids]
    
    # Add first video to each purchase and enrollment
    for purchase in purchases:
        first_video = None
        for day in purchase.course.curriculum_days.all().order_by('order', 'day_number'):
            videos = day.videos.all().order_by('order', 'id')
            if videos.exists():
                first_video = videos.first()
                break
        purchase.first_video = first_video
    
    for enrollment in enrollments:
        first_video = None
        for day in enrollment.course.curriculum_days.all().order_by('order', 'day_number'):
            videos = day.videos.all().order_by('order', 'id')
            if videos.exists():
                first_video = videos.first()
                break
        enrollment.first_video = first_video
    
    context = {
        'purchases': purchases,
        'enrollments': enrollments,
        'title': 'My Courses',
    }
    return render(request, 'lms/my_courses.html', context)


def video_player(request, video_id):
    """Enhanced video player view with curriculum and navigation"""
    video = get_object_or_404(
        Video.objects.select_related('curriculum_day__course'),
        id=video_id
    )
    
    # Check if user can access the video
    if not video.is_accessible_by(request.user):
        if not request.user.is_authenticated:
            messages.error(request, 'Please login to access this video.')
            return HttpResponseRedirect(f"{reverse('login')}?next={request.path}")
        else:
            messages.error(
                request,
                f'You need to purchase the course to access this video.'
            )
            return redirect('course_detail', slug=video.curriculum_day.course.slug)

    course = video.curriculum_day.course
    
    # Video progress tracking
    progress = None
    if request.user.is_authenticated:
        progress, _ = UserVideoProgress.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={
                'is_completed': False,
                'watched_percentage': 0,
                'watched_duration': 0
            }
        )
    
    # Get progress values
    is_completed = progress.is_completed if progress else False
    progress_percentage = progress.progress_percentage if progress else 0
    watched_duration = progress.watched_duration if progress else 0
    
    # Alias watched_percentage as progress_percentage for template compatibility
    watched_percentage = progress_percentage
    
    # Get all curriculum days with videos
    curriculum_days_qs = CurriculumDay.objects.filter(
        course=course
    ).prefetch_related('videos').order_by('order', 'day_number')
    
    curriculum_days = []
    all_videos_list = []
    
    # Calculate completed days
    completed_days = 0
    
    for day in curriculum_days_qs:
        day_videos = []
        day_completed_count = 0
        
        for vid in day.videos.all().order_by('order', 'id'):
            # Skip if video doesn't have an ID
            if not vid.id:
                continue
                
            vid_is_completed = False
            vid_progress_percentage = 0
            vid_watched_duration = 0
            
            if request.user.is_authenticated:
                vid_progress = UserVideoProgress.objects.filter(
                    user=request.user,
                    video=vid
                ).first()
                
                if vid_progress:
                    vid_is_completed = vid_progress.is_completed
                    vid_progress_percentage = vid_progress.progress_percentage or 0
                    vid_watched_duration = vid_progress.watched_duration or 0
                    
                    if vid_is_completed:
                        day_completed_count += 1
            
            video_data = {
                'id': vid.id,
                'title': vid.title,
                'duration': vid.duration or 0,
                'is_accessible': vid.is_accessible_by(request.user),
                'is_completed': vid_is_completed,
                'progress_percentage': vid_progress_percentage,
                'watched_percentage': vid_progress_percentage,  # Add watched_percentage alias
                'watched_duration': vid_watched_duration,
                'order': vid.order or 0
            }
            day_videos.append(video_data)
            all_videos_list.append(vid)
        
        # Calculate day progress percentage
        total_videos_in_day = len(day_videos)
        day_progress_percentage = int((day_completed_count / total_videos_in_day * 100)) if total_videos_in_day > 0 else 0
        
        # Check if day is completed
        if day_progress_percentage == 100:
            completed_days += 1
        
        curriculum_days.append({
            'id': day.id,
            'title': day.title,
            'videos': day_videos,
            'completed_videos': day_completed_count,
            'total_videos': total_videos_in_day,
            'progress_percentage': day_progress_percentage
        })
    
    # Find previous and next videos
    current_index = None
    for idx, vid in enumerate(all_videos_list):
        if vid.id == video.id:
            current_index = idx
            break
    
    previous_video = None
    next_video = None
    
    if current_index is not None:
        if current_index > 0:
            prev_vid = all_videos_list[current_index - 1]
            if prev_vid.is_accessible_by(request.user):
                previous_video = prev_vid
        
        if current_index < len(all_videos_list) - 1:
            next_vid = all_videos_list[current_index + 1]
            if next_vid.is_accessible_by(request.user):
                next_video = next_vid
    
    # Calculate course progress
    total_videos = len(all_videos_list)
    if request.user.is_authenticated:
        completed_videos = UserVideoProgress.objects.filter(
            user=request.user,
            video__in=all_videos_list,
            is_completed=True
        ).count()
        course_progress = int((completed_videos / total_videos * 100)) if total_videos > 0 else 0
    else:
        completed_videos = 0
        course_progress = 0

    context = {
        'video': video,
        'course': course,
        'progress': progress,
        'curriculum_days': curriculum_days,
        'current_day': video.curriculum_day,
        'previous_video': previous_video,
        'next_video': next_video,
        'course_progress': course_progress,
        'total_videos': total_videos,
        'completed_videos': completed_videos,
        'completed_days': completed_days,
        'is_completed': is_completed,
        'progress_percentage': progress_percentage,
        'watched_percentage': watched_percentage,  # Add to context
        'watched_duration': watched_duration,
    }

    return render(request, 'courses/video_player.html', context)

# def video_player(request, video_id):
#     """Enhanced video player view with curriculum and navigation"""
#     video = get_object_or_404(
#         Video.objects.select_related('curriculum_day__course'),
#         id=video_id
#     )


    
#     # Check if user can access the video
#     if not video.is_accessible_by(request.user):
#         if not request.user.is_authenticated:
#             messages.error(request, 'Please login to access this video.')
#             return HttpResponseRedirect(f"{reverse('login')}?next={request.path}")
#         else:
#             messages.error(
#                 request,
#                 f'You need to purchase the course to access this video.'
#             )
#             return redirect('course_detail', slug=video.curriculum_day.course.slug)

#     course = video.curriculum_day.course
    
#     # Video progress tracking
#     progress = None
#     if request.user.is_authenticated:
#         progress, _ = UserVideoProgress.objects.get_or_create(
#             user=request.user,
#             video=video,
#             defaults={'is_completed': False}
#         )

#     # Get all curriculum days with videos
#     curriculum_days_qs = CurriculumDay.objects.filter(
#         course=course
#     ).prefetch_related('videos').order_by('order', 'day_number')
    
#     curriculum_days = []
#     all_videos_list = []
    
#     for day in curriculum_days_qs:
#         day_videos = []
#         for vid in day.videos.all().order_by('order', 'id'):
#             is_completed = False
#             if request.user.is_authenticated:
#                 vid_progress = UserVideoProgress.objects.filter(
#                     user=request.user,
#                     video=vid
#                 ).first()
#                 if vid_progress:
#                     is_completed = vid_progress.is_completed
            
#             video_data = {
#                 'id': vid.id,
#                 'title': vid.title,
#                 'duration': vid.duration,
#                 'is_accessible': vid.is_accessible_by(request.user),
#                 'is_completed': is_completed,
#                 'order': vid.order
#             }
#             day_videos.append(video_data)
#             all_videos_list.append(vid)
        
#         curriculum_days.append({
#             'id': day.id,
#             'title': day.title,
#             'videos': day_videos
#         })
    
#     # Find previous and next videos
#     current_index = None
#     for idx, vid in enumerate(all_videos_list):
#         if vid.id == video.id:
#             current_index = idx
#             break
    
#     previous_video = None
#     next_video = None
    
#     if current_index is not None:
#         if current_index > 0:
#             prev_vid = all_videos_list[current_index - 1]
#             if prev_vid.is_accessible_by(request.user):
#                 previous_video = prev_vid
        
#         if current_index < len(all_videos_list) - 1:
#             next_vid = all_videos_list[current_index + 1]
#             if next_vid.is_accessible_by(request.user):
#                 next_video = next_vid
    
#     # Calculate course progress
#     if request.user.is_authenticated:
#         total_videos = len(all_videos_list)
#         completed_videos = UserVideoProgress.objects.filter(
#             user=request.user,
#             video__in=all_videos_list,
#             is_completed=True
#         ).count()
#         course_progress = int((completed_videos / total_videos * 100)) if total_videos > 0 else 0
#     else:
#         course_progress = 0
    


#     total_videos = len(all_videos_list)


#     completed_days = 0

#     for day in curriculum_days:
#         completed_videos_in_day = sum(
#             1 for v in day['videos'] if v['is_completed']
#         )
#         total_videos_in_day = len(day['videos'])
#     progress_percentage = int(
#         (completed_videos_in_day / total_videos_in_day) * 100
#     ) if total_videos_in_day else 0

#     day['progress_percentage'] = progress_percentage

#     if progress_percentage == 100:
#         completed_days += 1

#     completed_videos = UserVideoProgress.objects.filter(
#     user=request.user,
#     video__in=all_videos_list,
#     is_completed=True
# ).count() if request.user.is_authenticated else 0




#     context = {
#     'video': video,
#     'course': course,
#     'progress': progress,
#     'curriculum_days': curriculum_days,
#     'current_day': video.curriculum_day,
#     'previous_video': previous_video,
#     'next_video': next_video,
#     'course_progress': course_progress,
#     'total_videos': total_videos,
#     'completed_videos': completed_videos,
#     'completed_days': completed_days,
# }


#     return render(request, 'courses/video_player.html', context)




@login_required
def update_video_progress(request, video_id):
    video = get_object_or_404(Video, id=video_id)

    progress_percentage = int(request.POST.get('progress', 0))
    is_completed = request.POST.get('completed') == 'true'
    watched_seconds = int(request.POST.get('watched_seconds', 0))

    UserVideoProgress.objects.update_or_create(
        user=request.user,
        video=video,
        defaults={
            'progress_percentage': progress_percentage,
            'is_completed': is_completed,
            'watched_duration': watched_seconds
        }
    )

    return JsonResponse({'success': True})




@login_required
def enroll_course(request, slug):
    """Simple enrollment view"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    # Check if already enrolled
    if CourseEnrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, f'You are already enrolled in "{course.title}"')
        return redirect('course_detail', slug=slug)
    
    if request.method == 'POST':
        CourseEnrollment.objects.create(
            user=request.user, 
            course=course,
            enrollment_type='free',
            is_paid=False
        )
        messages.success(request, f'Successfully enrolled in "{course.title}"!')
        return redirect('my_courses')
    
    context = {
        'course': course,
    }
    return render(request, 'courses/enroll.html', context)


# ===== RAZORPAY PAYMENT VIEWS =====
@login_required
def checkout(request, slug):
    """Checkout page for course purchase using Razorpay"""
    course = get_object_or_404(Course, slug=slug, is_active=True)

    # Check if already purchased or enrolled
    if Purchase.objects.filter(user=request.user, course=course, payment_status='completed').exists():
        messages.info(request, f'You have already purchased "{course.title}"')
        return redirect('course_detail', slug=slug)

    if CourseEnrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, f'You are already enrolled in "{course.title}"')
        return redirect('course_detail', slug=slug)

    # Use discounted price
    base_price = float(course.discounted_price)
    
    tax_rate = 0.18
    tax_amount = round(base_price * tax_rate, 2)
    total_amount = round(base_price + tax_amount, 2)
    amount_paise = int(total_amount * 100)

    # Create Razorpay order
    order = razorpay_client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'payment_capture': '1',
    })

    # Create Payment record
    Payment.objects.create(
        user=request.user,
        course=course,
        razorpay_order_id=order['id'],
        amount=total_amount,
        currency='INR',
        status='pending'
    )

    context = {
        'course': course,
        'base_price': base_price,
        'tax_amount': tax_amount,
        'total_amount': total_amount,
        'razorpay_amount': amount_paise,
        'razorpay_order_id': order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
    }

    return render(request, 'courses/checkout.html', context)


@csrf_exempt
@login_required
def verify_payment(request):
    """Verify Razorpay payment"""
    if request.method != 'POST':
        return HttpResponse("Invalid request method", status=405)
    
    try:
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        course_slug = request.POST.get('course_slug')
        
        course = get_object_or_404(Course, slug=course_slug, is_active=True)
        payment = Payment.objects.get(
            razorpay_order_id=razorpay_order_id,
            user=request.user
        )
        
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'success'
        payment.payment_date = timezone.now()
        
        # Save billing info
        payment.billing_first_name = request.POST.get('first_name', '')
        payment.billing_last_name = request.POST.get('last_name', '')
        payment.billing_email = request.POST.get('email', '')
        payment.billing_phone = request.POST.get('phone', '')
        payment.billing_address = request.POST.get('address', '')
        payment.billing_city = request.POST.get('city', '')
        payment.billing_state = request.POST.get('state', '')
        payment.billing_zip_code = request.POST.get('zip_code', '')
        payment.billing_country = request.POST.get('country', 'IN')
        payment.notes = request.POST.get('notes', '')
        payment.payment_method = request.POST.get('payment_method', 'card')
        
        payment.save()
        
        # Create Purchase record (new system)
        Purchase.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'amount_paid': payment.amount,
                'payment_status': 'completed',
                'transaction_id': razorpay_payment_id,
                'full_name': f"{payment.billing_first_name} {payment.billing_last_name}",
                'email': payment.billing_email or request.user.email
            }
        )
        
        # Also create enrollment (legacy system)
        CourseEnrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'enrollment_type': 'paid',
                'is_paid': True,
                'transaction_id': razorpay_payment_id
            }
        )
        
        messages.success(request, f'Successfully enrolled in {course.title}!')
        return redirect('course_detail', slug=course.slug)
        
    except razorpay.errors.SignatureVerificationError as e:
        messages.error(request, "Payment verification failed.")
        return redirect('payment_failed')
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('payment_failed')
    except Exception as e:
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('payment_failed')
    



@login_required
def payment_success(request):
    """Payment success page"""
    order_id = request.GET.get('order_id')
    
    try:
        if order_id:
            payment = Payment.objects.filter(
                razorpay_order_id=order_id,
                user=request.user,
                status='success'
            ).first()
            
            if payment:
                context = {
                    'course': payment.course,
                    'payment': payment,
                    'user': request.user,
                }
                return render(request, 'courses/payment_success.html', context)
        
        recent_payment = Payment.objects.filter(
            user=request.user,
            status='success'
        ).order_by('-payment_date').first()
        
        if recent_payment:
            context = {
                'course': recent_payment.course,
                'payment': recent_payment,
                'user': request.user,
            }
            return render(request, 'courses/payment_success.html', context)
        
        messages.info(request, 'No successful payment found.')
        return redirect('all_courses')
        
    except Exception as e:
        messages.error(request, f'Error: {str(e)}')
        return redirect('all_courses')


@login_required
def payment_failed(request):
    """Payment failed page"""
    error_code = request.GET.get('error_code', 'Unknown')
    error_desc = request.GET.get('error_description', 'Payment failed')
    
    context = {
        'error_code': error_code,
        'error_desc': error_desc,
        'user': request.user,
    }
    return render(request, 'courses/payment_failed.html', context)


@csrf_exempt
@login_required
def create_razorpay_order(request, slug):
    """Create Razorpay order via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
    try:
        course = get_object_or_404(Course, slug=slug, is_active=True)
        
        # Check if already purchased
        if Purchase.objects.filter(user=request.user, course=course, payment_status='completed').exists():
            return JsonResponse({
                'success': False,
                'error': 'Already purchased this course'
            }, status=400)
        
        if CourseEnrollment.objects.filter(user=request.user, course=course).exists():
            return JsonResponse({
                'success': False,
                'error': 'Already enrolled in this course'
            }, status=400)
        
        amount = float(course.discounted_price)
        amount_paise = int(amount * 100)
        
        order_data = {
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': '1',
        }
        
        order = razorpay_client.order.create(data=order_data)
        
        Payment.objects.create(
            user=request.user,
            course=course,
            razorpay_order_id=order['id'],
            amount=amount,
            currency='INR',
            status='pending',
            created_at=timezone.now()
        )
        
        return JsonResponse({
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency']
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


@csrf_exempt
@login_required
def create_test_payment(request, slug):
    """Create test payment for development"""
    if not settings.DEBUG:
        return JsonResponse({'success': False, 'error': 'Not allowed in production'}, status=403)
    
    try:
        course = get_object_or_404(Course, slug=slug, is_active=True)
        
        # Check if already purchased
        if Purchase.objects.filter(user=request.user, course=course, payment_status='completed').exists():
            return JsonResponse({
                'success': False,
                'error': 'Already purchased this course'
            }, status=400)
        
        test_order_id = f'test_order_{uuid.uuid4().hex[:10]}'
        test_payment_id = f'test_payment_{uuid.uuid4().hex[:10]}'
        
        amount = float(course.discounted_price)
        
        # Create Payment record
        payment = Payment.objects.create(
            user=request.user,
            course=course,
            razorpay_order_id=test_order_id,
            razorpay_payment_id=test_payment_id,
            amount=amount,
            currency='INR',
            status='success',
            payment_method='test',
            payment_date=timezone.now(),
            created_at=timezone.now()
        )
        
        # Create Purchase record (new system)
        Purchase.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'amount_paid': amount,
                'payment_status': 'completed',
                'transaction_id': test_payment_id,
                'full_name': request.user.get_full_name() or request.user.username,
                'email': request.user.email
            }
        )
        
        # Create enrollment (legacy system)
        CourseEnrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={
                'enrollment_type': 'paid',
                'is_paid': True,
                'transaction_id': test_payment_id
            }
        )
        
        return JsonResponse({
            'success': True,
            'redirect_url': f'/courses/{course.slug}/'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


# ===== OTHER PAGES =====
def placeholder_view(request, page_name=None):
    """Catch-all for pages not implemented yet"""
    page_titles = {
        'about': 'About Us',
        'contact': 'Contact Us',
        'privacy': 'Privacy Policy',
        'terms': 'Terms & Conditions',
    }
    
    title = page_titles.get(page_name, page_name.replace('-', ' ').title() if page_name else 'Page')
    
    return render(request, 'lms/placeholder.html', {
        'title': title,
        'message': f'The {title} page is coming soon!'
    })


def about_us(request):
    """About Us page"""
    return render(request, 'lms/about.html', {
        'title': 'About Us',
        'message': 'Learn more about our e-learning platform.'
    })


from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ContactForm

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your message has been sent successfully!")
            return redirect('contact')
    else:
        form = ContactForm()

    return render(request, 'lms/contact.html', {'form': form})



def privacy_policy(request):
    """Privacy Policy page"""
    return render(request, "privacy_policy.html")


def terms_of_use(request):
    """Terms of Use page"""
    return render(request, "terms_of_use.html")




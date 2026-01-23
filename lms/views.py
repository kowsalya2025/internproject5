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

from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Prefetch
from django.conf import settings
from .models import (
    Course, CurriculumDay, Purchase, UserVideoProgress, 
    CourseReview  # Use your existing CourseReview model
)

@require_http_methods(["GET", "POST"])
def course_detail(request, slug):
    """Display course detail page with curriculum and handle review submissions"""
    
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

    # Handle AJAX POST requests (Review Submission)
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        action = request.POST.get('action')
        
        if action == 'submit_review':
            try:
                # Validate required fields
                name = request.POST.get('name', '').strip()
                rating = request.POST.get('rating')
                review_text = request.POST.get('review', '').strip()
                
                if not name:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Name is required'
                    })
                
                if not rating:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Please select a rating'
                    })
                
                if not review_text:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Review text is required'
                    })
                
                # Validate rating value
                try:
                    rating_value = int(rating)
                    if rating_value < 1 or rating_value > 5:
                        return JsonResponse({
                            'success': False, 
                            'error': 'Rating must be between 1 and 5'
                        })
                except ValueError:
                    return JsonResponse({
                        'success': False, 
                        'error': 'Invalid rating value'
                    })
                
                # Check if user already reviewed this course (optional)
                if request.user.is_authenticated:
                    existing_review = CourseReview.objects.filter(
                        user=request.user,
                        course=course
                    ).first()
                    
                    if existing_review:
                        return JsonResponse({
                            'success': False, 
                            'error': 'You have already reviewed this course'
                        })
                
                # Create review
                review = CourseReview.objects.create(
                    course=course,
                    name=name,
                    rating=rating_value,
                    review=review_text,
                    user=request.user if request.user.is_authenticated else None,
                    # Set to True if you don't need moderation, False if you do
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': 'Thank you! Your review has been submitted successfully.'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'An error occurred: {str(e)}'
                })

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
            'is_free': day.is_free if hasattr(day, 'is_free') else False,
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
                'is_completed': is_completed,
                'video_url': video.video_file.url if hasattr(video, 'video_file') and video.video_file else ''
            })

        curriculum_days.append(day_data)

    # Get reviews - adjust based on your CourseReview model fields
    reviews = CourseReview.objects.filter(
        course=course
    ).select_related('user').order_by('-created_at')[:10]

    context = {
        'course': course,
        'curriculum_days': curriculum_days,
        'user_has_paid': user_has_paid,
        'first_video': first_video,
        'discount_percentage': course.get_discount_percentage(),
        'skills_list': course.get_skills_list(),
        'tools_list': course.get_tools_list(),
        'reviews': reviews,
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

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Purchase, CourseEnrollment, CourseProgress, Certificate

@login_required
def my_courses(request):
    """Display user's purchased and enrolled courses with first video, progress, and certificate"""

    # Purchases
    purchases = Purchase.objects.filter(
        user=request.user,
        payment_status='completed'
    ).select_related('course__category').prefetch_related(
        'course__instructors',
        'course__curriculum_days__videos'
    ).order_by('-purchased_at')

    # Legacy enrollments
    enrollments = CourseEnrollment.objects.filter(
        user=request.user
    ).select_related('course__category').prefetch_related(
        'course__instructors',
        'course__curriculum_days__videos'
    ).order_by('-enrolled_at')

    # Filter out enrollments that are already purchased
    purchased_course_ids = [p.course.id for p in purchases]
    enrollments = [e for e in enrollments if e.course.id not in purchased_course_ids]

    # Collect all course IDs for bulk fetching progress and certificates
    all_courses = [p.course for p in purchases] + [e.course for e in enrollments]
    course_ids = [c.id for c in all_courses]

    # Bulk fetch progress and certificates
    progress_map = {cp.course_id: cp for cp in CourseProgress.objects.filter(user=request.user, course_id__in=course_ids)}
    certificate_map = {cert.course_id: cert for cert in Certificate.objects.filter(user=request.user, course_id__in=course_ids)}

    # Assign first video, progress, certificate
    def enhance_course(obj):
        first_video = None
        for day in obj.course.curriculum_days.all().order_by('order', 'day_number'):
            videos = day.videos.all().order_by('order', 'id')
            if videos.exists():
                first_video = videos.first()
                break
        obj.first_video = first_video
        obj.progress = progress_map.get(obj.course.id)
        obj.certificate = certificate_map.get(obj.course.id)

    for p in purchases:
        enhance_course(p)
    for e in enrollments:
        enhance_course(e)

    context = {
        'purchases': purchases,
        'enrollments': enrollments,
        'title': 'My Courses',
    }

    return render(request, 'lms/my_courses.html', context)


# def video_player(request, video_id):
#     """Enhanced video player view with curriculum and navigation"""

#     video = get_object_or_404(
#         Video.objects.select_related('curriculum_day__course'),
#         id=video_id
#     )

#     # Access control
#     if not video.is_accessible_by(request.user):
#         if not request.user.is_authenticated:
#             messages.error(request, 'Please login to access this video.')
#             return HttpResponseRedirect(f"{reverse('login')}?next={request.path}")
#         messages.error(request, 'You need to purchase the course to access this video.')
#         return redirect('course_detail', slug=video.curriculum_day.course.slug)

#     course = video.curriculum_day.course

#     # -------------------------------
#     # Video-level progress
#     # -------------------------------
#     progress = None
#     if request.user.is_authenticated:
#         progress, _ = UserVideoProgress.objects.get_or_create(
#             user=request.user,
#             video=video,
#             defaults={
#                 'is_completed': False,
#                 'watched_percentage': 0,
#                 'watched_duration': 0
#             }
#         )

#     is_completed = progress.is_completed if progress else False
#     progress_percentage = progress.progress_percentage if progress else 0
#     watched_percentage = progress_percentage
#     watched_duration = progress.watched_duration if progress else 0

#     # -------------------------------
#     # Curriculum + video listing
#     # -------------------------------
#     curriculum_days = []
#     all_videos_list = []
#     completed_days = 0

#     curriculum_days_qs = CurriculumDay.objects.filter(
#         course=course
#     ).prefetch_related('videos').order_by('order', 'day_number')

#     for day in curriculum_days_qs:
#         day_videos = []
#         day_completed_count = 0

#         for vid in day.videos.all().order_by('order', 'id'):
#             vid_progress = None
#             if request.user.is_authenticated:
#                 vid_progress = UserVideoProgress.objects.filter(
#                     user=request.user,
#                     video=vid
#                 ).first()

#             vid_is_completed = vid_progress.is_completed if vid_progress else False
#             vid_progress_percentage = vid_progress.progress_percentage if vid_progress else 0
#             vid_watched_duration = vid_progress.watched_duration if vid_progress else 0

#             if vid_is_completed:
#                 day_completed_count += 1

#             day_videos.append({
#                 'id': vid.id,
#                 'title': vid.title,
#                 'duration': vid.duration or 0,
#                 'is_accessible': vid.is_accessible_by(request.user),
#                 'is_completed': vid_is_completed,
#                 'progress_percentage': vid_progress_percentage,
#                 'watched_percentage': vid_progress_percentage,
#                 'watched_duration': vid_watched_duration,
#                 'order': vid.order or 0
#             })

#             all_videos_list.append(vid)

#         total_videos_in_day = len(day_videos)
#         day_progress_percentage = int(
#             (day_completed_count / total_videos_in_day) * 100
#         ) if total_videos_in_day else 0

#         if day_progress_percentage == 100:
#             completed_days += 1

#         curriculum_days.append({
#             'id': day.id,
#             'title': day.title,
#             'videos': day_videos,
#             'completed_videos': day_completed_count,
#             'total_videos': total_videos_in_day,
#             'progress_percentage': day_progress_percentage
#         })

#     # -------------------------------
#     # Previous / Next video
#     # -------------------------------
#     previous_video = next_video = None
#     try:
#         idx = all_videos_list.index(video)
#         if idx > 0 and all_videos_list[idx - 1].is_accessible_by(request.user):
#             previous_video = all_videos_list[idx - 1]
#         if idx < len(all_videos_list) - 1 and all_videos_list[idx + 1].is_accessible_by(request.user):
#             next_video = all_videos_list[idx + 1]
#     except ValueError:
#         pass

#     # -------------------------------
#     # Course progress
#     # -------------------------------
#     total_videos = len(all_videos_list)
#     completed_videos = 0
#     course_progress = 0

#     if request.user.is_authenticated:
#         completed_videos = UserVideoProgress.objects.filter(
#             user=request.user,
#             video__in=all_videos_list,
#             is_completed=True
#         ).count()
#         course_progress = int((completed_videos / total_videos) * 100) if total_videos else 0

#     # -------------------------------
#     # Course-level quiz status & certificate
#     # -------------------------------
#     quiz_passed = False
#     has_quiz = False
#     course_completed = False
#     certificate = None
    
#     if request.user.is_authenticated:
#         # Get or create course progress (for quiz tracking)
#         course_progress_obj, _ = CourseProgress.objects.get_or_create(
#             user=request.user,
#             course=course
#         )
        
#         # Update course progress with completed videos
#         # Sync UserVideoProgress with CourseProgress
#         completed_video_objects = [v for v in all_videos_list if UserVideoProgress.objects.filter(
#             user=request.user,
#             video=v,
#             is_completed=True
#         ).exists()]
        
#         course_progress_obj.completed_videos.set(completed_video_objects)
#         course_progress_obj.update_progress()
        
#         # Check quiz status
#         quiz_passed = course_progress_obj.quiz_passed
        
#         # Check if course has a quiz
#         try:
#             has_quiz = hasattr(course, 'quiz') and course.quiz is not None
#         except:
#             has_quiz = False
        
#         # Check if course is completed (all videos + quiz passed)
#         course_completed = course_progress_obj.is_completed
        
#         # Get certificate if exists
#         if course_completed:
#             try:
#                 certificate = Certificate.objects.get(
#                     user=request.user,
#                     course=course
#                 )
#             except Certificate.DoesNotExist:
#                 certificate = None

#     # -------------------------------
#     # Context
#     # -------------------------------
#     context = {
#         'video': video,
#         'course': course,
#         'progress': progress,
#         'curriculum_days': curriculum_days,
#         'current_day': video.curriculum_day,
#         'previous_video': previous_video,
#         'next_video': next_video,

#         'course_progress': course_progress,
#         'total_videos': total_videos,
#         'completed_videos': completed_videos,
#         'completed_days': completed_days,

#         'is_completed': is_completed,
#         'progress_percentage': progress_percentage,
#         'watched_percentage': watched_percentage,
#         'watched_duration': watched_duration,

#         # Quiz & Certificate
#         'quiz_passed': quiz_passed,
#         'has_quiz': has_quiz,
#         'course_completed': course_completed,
#         'certificate': certificate,
#     }

#     return render(request, 'courses/video_player.html', context)
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages

from lms.models import (
    Video,
    CurriculumDay,
    UserVideoProgress,
    CourseProgress,
    Certificate,
)


def video_player(request, video_id):
    """
    Video player view (READ-ONLY for course & quiz state)
    Safe for GET requests – no quiz validation or writes.
    """

    # -------------------------------------------------
    # Video + course
    # -------------------------------------------------
    video = get_object_or_404(
        Video.objects.select_related("curriculum_day__course"),
        id=video_id,
    )

    course = video.curriculum_day.course

    # -------------------------------------------------
    # Access control
    # -------------------------------------------------
    if not video.is_accessible_by(request.user):
        if not request.user.is_authenticated:
            messages.error(request, "Please login to access this video.")
            return HttpResponseRedirect(
                f"{reverse('login')}?next={request.path}"
            )

        messages.error(
            request,
            "You need to purchase the course to access this video.",
        )
        return redirect("course_detail", slug=course.slug)

    # -------------------------------------------------
    # Current video progress
    # -------------------------------------------------
    progress = None
    is_completed = False
    progress_percentage = 0
    watched_percentage = 0
    watched_duration = 0

    if request.user.is_authenticated:
        progress, _ = UserVideoProgress.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={
                "is_completed": False,
                "watched_percentage": 0,
                "watched_duration": 0,
            },
        )

        is_completed = progress.is_completed
        progress_percentage = progress.progress_percentage
        watched_percentage = progress.progress_percentage
        watched_duration = progress.watched_duration

    # -------------------------------------------------
    # Curriculum + video listing
    # -------------------------------------------------
    curriculum_days = []
    all_videos_list = []
    completed_days = 0

    curriculum_days_qs = (
        CurriculumDay.objects.filter(course=course)
        .prefetch_related("videos")
        .order_by("order", "day_number")
    )

    for day in curriculum_days_qs:
        day_videos = []
        completed_count = 0

        for vid in day.videos.all().order_by("order", "id"):
            vid_progress = None

            if request.user.is_authenticated:
                vid_progress = UserVideoProgress.objects.filter(
                    user=request.user,
                    video=vid,
                ).first()

            vid_completed = vid_progress.is_completed if vid_progress else False
            vid_percentage = (
                vid_progress.progress_percentage if vid_progress else 0
            )
            vid_duration = (
                vid_progress.watched_duration if vid_progress else 0
            )

            if vid_completed:
                completed_count += 1

            day_videos.append(
                {
                    "id": vid.id,
                    "title": vid.title,
                    "duration": vid.duration or 0,
                    "is_accessible": vid.is_accessible_by(request.user),
                    "is_completed": vid_completed,
                    "progress_percentage": vid_percentage,
                    "watched_percentage": vid_percentage,
                    "watched_duration": vid_duration,
                    "order": vid.order or 0,
                }
            )

            all_videos_list.append(vid)

        total_videos_in_day = len(day_videos)
        day_progress_percentage = (
            int((completed_count / total_videos_in_day) * 100)
            if total_videos_in_day
            else 0
        )

        if day_progress_percentage == 100:
            completed_days += 1

        curriculum_days.append(
            {
                "id": day.id,
                "title": day.title,
                "videos": day_videos,
                "completed_videos": completed_count,
                "total_videos": total_videos_in_day,
                "progress_percentage": day_progress_percentage,
            }
        )

    # -------------------------------------------------
    # Previous / Next video
    # -------------------------------------------------
    previous_video = None
    next_video = None

    try:
        idx = all_videos_list.index(video)

        if idx > 0:
            prev = all_videos_list[idx - 1]
            if prev.is_accessible_by(request.user):
                previous_video = prev

        if idx < len(all_videos_list) - 1:
            nxt = all_videos_list[idx + 1]
            if nxt.is_accessible_by(request.user):
                next_video = nxt

    except ValueError:
        pass

    # -------------------------------------------------
    # Course progress (READ ONLY)
    # -------------------------------------------------
    total_videos = len(all_videos_list)
    completed_videos = 0
    course_progress = 0

    if request.user.is_authenticated:
        completed_videos = UserVideoProgress.objects.filter(
            user=request.user,
            video__in=all_videos_list,
            is_completed=True,
        ).count()

        course_progress = (
            int((completed_videos / total_videos) * 100)
            if total_videos
            else 0
        )

    # -------------------------------------------------
    # Quiz & certificate status (NO VALIDATION)
    # -------------------------------------------------
    quiz_passed = False
    has_quiz = False
    course_completed = False
    certificate = None

    if request.user.is_authenticated:
        course_progress_obj, _ = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course,
        )

        quiz_passed = course_progress_obj.quiz_passed
        course_completed = course_progress_obj.is_completed
        has_quiz = hasattr(course, "quiz") and course.quiz is not None

        if course_completed:
            certificate = Certificate.objects.filter(
                user=request.user,
                course=course,
            ).first()

    # -------------------------------------------------
    # Context
    # -------------------------------------------------
    context = {
        "video": video,
        "course": course,
        "progress": progress,
        "curriculum_days": curriculum_days,
        "current_day": video.curriculum_day,
        "previous_video": previous_video,
        "next_video": next_video,
        "course_progress": course_progress,
        "total_videos": total_videos,
        "completed_videos": completed_videos,
        "completed_days": completed_days,
        "is_completed": is_completed,
        "progress_percentage": progress_percentage,
        "watched_percentage": watched_percentage,
        "watched_duration": watched_duration,
        "quiz_passed": quiz_passed,
        "has_quiz": has_quiz,
        "course_completed": course_completed,
        "certificate": certificate,
    }

    return render(request, "courses/video_player.html", context)



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

    # DEBUG PRINTS - Check terminal for these
    print("="*50)
    print(f"CHECKOUT DEBUG:")
    print(f"Course: {course.title}")
    print(f"Base Price: ₹{base_price}")
    print(f"Tax Amount: ₹{tax_amount}")
    print(f"Total Amount: ₹{total_amount}")
    print(f"Amount in Paise: {amount_paise}")
    print(f"Razorpay Key ID: {settings.RAZORPAY_KEY_ID[:10]}...")  # Only show first 10 chars
    print("="*50)

    # Create Razorpay order WITH ERROR HANDLING
    try:
        order = razorpay_client.order.create({
            'amount': amount_paise,
            'currency': 'INR',
            'payment_capture': '1',
        })
        
        print(f"✓ Razorpay Order Created Successfully!")
        print(f"Order ID: {order['id']}")
        print("="*50)
        
    except Exception as e:
        print("="*50)
        print(f"✗ RAZORPAY ERROR:")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print("="*50)
        messages.error(request, f'Unable to create payment order. Please try again later.')
        return redirect('course_detail', slug=slug)

    # Create Payment record
    try:
        Payment.objects.create(
            user=request.user,
            course=course,
            razorpay_order_id=order['id'],
            amount=total_amount,
            currency='INR',
            status='pending'
        )
        print(f"✓ Payment record created in database")
    except Exception as e:
        print(f"✗ Database Error: {str(e)}")

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


from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect  # enable CSRF
from .models import Course, Payment, Purchase, CourseEnrollment
import razorpay


@csrf_protect
def verify_payment(request):
    """Verify Razorpay payment from browser checkout"""
    if request.method != 'POST':
        return HttpResponse("Invalid request method", status=405)
    
    try:
        # Razorpay fields
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')
        course_slug = request.POST.get('course_slug')
        
        course = get_object_or_404(Course, slug=course_slug, is_active=True)
        
        # Get Payment record linked to user & order
        payment = Payment.objects.get(
            razorpay_order_id=razorpay_order_id,
            user=request.user
        )
        
        # Verify signature
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }
        razorpay_client.utility.verify_payment_signature(params_dict)
        
        # Update Payment object
        payment.razorpay_payment_id = razorpay_payment_id
        payment.razorpay_signature = razorpay_signature
        payment.status = 'success'
        payment.payment_date = timezone.now()
        
        # Save billing info from form
        payment.billing_first_name = request.POST.get('first_name', '')
        payment.billing_last_name = request.POST.get('last_name', '')
        payment.billing_email = request.POST.get('email', '')
        payment.billing_phone = request.POST.get('phone', '')
        payment.billing_address = request.POST.get('address', '')
        payment.billing_city = request.POST.get('city', '')
        payment.billing_state = request.POST.get('state', '')
        payment.billing_zip_code = request.POST.get('zip_code', '')
        payment.billing_country = request.POST.get('country', 'IN')
        payment.payment_method = request.POST.get('payment_method', 'card')
        payment.save()
        
        # Create Purchase record
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
        
        # Create CourseEnrollment
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
    
    except razorpay.errors.SignatureVerificationError:
        messages.error(request, "Payment verification failed.")
        return redirect('payment_failed')
    except Payment.DoesNotExist:
        messages.error(request, "Payment record not found.")
        return redirect('payment_failed')
    except Exception as e:
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('payment_failed')


# @csrf_exempt
# def verify_payment(request):
#     """Verify Razorpay payment"""
#     if request.method != 'POST':
#         return HttpResponse("Invalid request method", status=405)
    
#     try:
#         razorpay_order_id = request.POST.get('razorpay_order_id')
#         razorpay_payment_id = request.POST.get('razorpay_payment_id')
#         razorpay_signature = request.POST.get('razorpay_signature')
#         course_slug = request.POST.get('course_slug')
        
#         course = get_object_or_404(Course, slug=course_slug, is_active=True)
#         payment = Payment.objects.get(
#             razorpay_order_id=razorpay_order_id,
#             user=request.user
#         )
        
#         params_dict = {
#             'razorpay_order_id': razorpay_order_id,
#             'razorpay_payment_id': razorpay_payment_id,
#             'razorpay_signature': razorpay_signature
#         }
        
#         razorpay_client.utility.verify_payment_signature(params_dict)
        
#         payment.razorpay_payment_id = razorpay_payment_id
#         payment.razorpay_signature = razorpay_signature
#         payment.status = 'success'
#         payment.payment_date = timezone.now()
        
#         # Save billing info
#         payment.billing_first_name = request.POST.get('first_name', '')
#         payment.billing_last_name = request.POST.get('last_name', '')
#         payment.billing_email = request.POST.get('email', '')
#         payment.billing_phone = request.POST.get('phone', '')
#         payment.billing_address = request.POST.get('address', '')
#         payment.billing_city = request.POST.get('city', '')
#         payment.billing_state = request.POST.get('state', '')
#         payment.billing_zip_code = request.POST.get('zip_code', '')
#         payment.billing_country = request.POST.get('country', 'IN')
#         payment.notes = request.POST.get('notes', '')
#         payment.payment_method = request.POST.get('payment_method', 'card')
        
#         payment.save()
        
#         # Create Purchase record (new system)
#         Purchase.objects.get_or_create(
#             user=request.user,
#             course=course,
#             defaults={
#                 'amount_paid': payment.amount,
#                 'payment_status': 'completed',
#                 'transaction_id': razorpay_payment_id,
#                 'full_name': f"{payment.billing_first_name} {payment.billing_last_name}",
#                 'email': payment.billing_email or request.user.email
#             }
#         )
        
#         # Also create enrollment (legacy system)
#         CourseEnrollment.objects.get_or_create(
#             user=request.user,
#             course=course,
#             defaults={
#                 'enrollment_type': 'paid',
#                 'is_paid': True,
#                 'transaction_id': razorpay_payment_id
#             }
#         )
        
#         messages.success(request, f'Successfully enrolled in {course.title}!')
#         return redirect('course_detail', slug=course.slug)
        
#     except razorpay.errors.SignatureVerificationError as e:
#         messages.error(request, "Payment verification failed.")
#         return redirect('payment_failed')
#     except Payment.DoesNotExist:
#         messages.error(request, "Payment record not found.")
#         return redirect('payment_failed')
#     except Exception as e:
#         messages.error(request, f"Payment error: {str(e)}")
#         return redirect('payment_failed')
    



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


from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

@csrf_exempt
def razorpay_callback(request):
    """
    Razorpay webhook endpoint for payment confirmation.
    Razorpay sends POST requests here after payment.
    """
    if request.method != "POST":
        return JsonResponse({"status": "invalid method"}, status=405)

    try:
        # Optional: log incoming data for debugging
        print("Razorpay callback received:", request.POST)

        # You can optionally call your existing verify_payment logic here
        # For example, you could call:
        # return verify_payment(request)

        # Or just respond OK for testing:
        return JsonResponse({"status": "success"})

    except Exception as e:
        print("Razorpay callback error:", str(e))
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# @csrf_exempt
# @login_required
# def create_razorpay_order(request, slug):
#     """Create Razorpay order via AJAX"""
#     if request.method != 'POST':
#         return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)
    
#     try:
#         course = get_object_or_404(Course, slug=slug, is_active=True)
        
#         # Check if already purchased
#         if Purchase.objects.filter(user=request.user, course=course, payment_status='completed').exists():
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Already purchased this course'
#             }, status=400)
        
#         if CourseEnrollment.objects.filter(user=request.user, course=course).exists():
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Already enrolled in this course'
#             }, status=400)
        
#         amount = float(course.discounted_price)
#         amount_paise = int(amount * 100)
        
#         order_data = {
#             'amount': amount_paise,
#             'currency': 'INR',
#             'payment_capture': '1',
#         }
        
#         order = razorpay_client.order.create(data=order_data)
        
#         Payment.objects.create(
#             user=request.user,
#             course=course,
#             razorpay_order_id=order['id'],
#             amount=amount,
#             currency='INR',
#             status='pending',
#             created_at=timezone.now()
#         )
        
#         return JsonResponse({
#             'success': True,
#             'order_id': order['id'],
#             'amount': order['amount'],
#             'currency': order['currency']
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=400)


# @csrf_exempt
# @login_required
# def create_test_payment(request, slug):
#     """Create test payment for development"""
#     if not settings.DEBUG:
#         return JsonResponse({'success': False, 'error': 'Not allowed in production'}, status=403)
    
#     try:
#         course = get_object_or_404(Course, slug=slug, is_active=True)
        
#         # Check if already purchased
#         if Purchase.objects.filter(user=request.user, course=course, payment_status='completed').exists():
#             return JsonResponse({
#                 'success': False,
#                 'error': 'Already purchased this course'
#             }, status=400)
        
#         test_order_id = f'test_order_{uuid.uuid4().hex[:10]}'
#         test_payment_id = f'test_payment_{uuid.uuid4().hex[:10]}'
        
#         amount = float(course.discounted_price)
        
#         # Create Payment record
#         payment = Payment.objects.create(
#             user=request.user,
#             course=course,
#             razorpay_order_id=test_order_id,
#             razorpay_payment_id=test_payment_id,
#             amount=amount,
#             currency='INR',
#             status='success',
#             payment_method='test',
#             payment_date=timezone.now(),
#             created_at=timezone.now()
#         )
        
#         # Create Purchase record (new system)
#         Purchase.objects.get_or_create(
#             user=request.user,
#             course=course,
#             defaults={
#                 'amount_paid': amount,
#                 'payment_status': 'completed',
#                 'transaction_id': test_payment_id,
#                 'full_name': request.user.get_full_name() or request.user.username,
#                 'email': request.user.email
#             }
#         )
        
#         # Create enrollment (legacy system)
#         CourseEnrollment.objects.get_or_create(
#             user=request.user,
#             course=course,
#             defaults={
#                 'enrollment_type': 'paid',
#                 'is_paid': True,
#                 'transaction_id': test_payment_id
#             }
#         )
        
#         return JsonResponse({
#             'success': True,
#             'redirect_url': f'/courses/{course.slug}/'
#         })
        
#     except Exception as e:
#         return JsonResponse({
#             'success': False,
#             'error': str(e)
#         }, status=400)


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



# quezz
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from .models import (
    Quiz, QuizAttempt, QuizResponse, Question, Answer,
    CourseProgress, Certificate, Course
)

@login_required
def quiz_start(request, course_slug):
    """Display quiz instructions and start quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    
    try:
        quiz = course.quiz
    except Quiz.DoesNotExist:
        messages.error(request, "This course doesn't have a quiz yet.")
        return redirect('course_detail', slug=course_slug)
    
    # -----------------------
    # Check if user has access
    # -----------------------
    has_access = (
        request.user.purchases.filter(course=course).exists() or
        request.user.enrollments.filter(course=course).exists()
    )
    
    if not has_access:
        messages.error(request, "You need to enroll in this course first.")
        return redirect('course_detail', slug=course_slug)

    # -----------------------
    # NEW: Ensure all videos completed before quiz
    # -----------------------
    if request.user.is_authenticated:
        course_progress_obj, _ = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        if course_progress_obj.progress_percentage < 100:
            messages.error(request, "You must complete all course videos before taking the quiz.")
            return redirect('course_detail', slug=course_slug)
    
    # -----------------------
    # Check previous attempts
    # -----------------------
    attempts = QuizAttempt.objects.filter(user=request.user, quiz=quiz)
    attempts_count = attempts.count()
    best_score = attempts.filter(passed=True).order_by('-score').first()
    
    # ... rest of your view ...

    
    # Check if max attempts reached
    if quiz.max_attempts > 0 and attempts_count >= quiz.max_attempts:
        if not best_score:
            messages.error(request, f"You have used all {quiz.max_attempts} attempts.")
            return redirect('course_detail', slug=course_slug)
    
    context = {
        'course': course,
        'quiz': quiz,
        'attempts_count': attempts_count,
        'attempts_left': quiz.max_attempts - attempts_count if quiz.max_attempts > 0 else None,
        'best_score': best_score,
        'total_questions': quiz.get_total_questions(),
    }
    
    return render(request, 'lms/quiz_start.html', context)


@login_required
def quiz_take(request, course_slug):
    """Take the quiz"""
    course = get_object_or_404(Course, slug=course_slug)
    quiz = get_object_or_404(Quiz, course=course)
    
    # Create new attempt
    attempt = QuizAttempt.objects.create(
        user=request.user,
        quiz=quiz
    )
    
    questions = quiz.questions.prefetch_related('answers').all()
    
    context = {
        'course': course,
        'quiz': quiz,
        'attempt': attempt,
        'questions': questions,
    }
    
    return render(request, 'lms/quiz_take.html', context)


from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages

def quiz_submit(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)

    if request.method != "POST":
        return redirect("quiz_take", attempt.quiz.id)

    # Prevent resubmission
    if attempt.completed_at:
        messages.error(request, "This quiz attempt is already submitted.")
        return redirect("quiz_result", attempt.id)

    for question in attempt.quiz.questions.all():
        key = f"question_{question.id}"
        selected_ids = request.POST.getlist(key)

        if not selected_ids:
            continue  # unanswered question

        # Validate answers belong to this question
        answers = Answer.objects.filter(
            id__in=selected_ids,
            question=question
        )

        if not answers.exists():
            continue

        response = QuizResponse.objects.create(
            attempt=attempt,
            question=question
        )

        response.selected_answers.set(answers)

    # Mark attempt completed
    attempt.completed_at = timezone.now()
    attempt.calculate_score()

    messages.success(request, "Quiz submitted successfully.")
    return redirect("quiz_result", attempt.id)



@login_required
def quiz_result(request, attempt_id):
    """Display quiz results"""
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, user=request.user)
    
    responses = attempt.responses.prefetch_related(
        'question__answers',
        'selected_answers'
    ).all()
    
    # Prepare detailed results and count correct/incorrect
    results = []
    correct_count = 0
    incorrect_count = 0
    
    for response in responses:
        question = response.question
        correct_answers = question.answers.filter(is_correct=True)
        selected_answers = response.selected_answers.all()
        is_correct = response.is_correct()
        
        # Count correct/incorrect answers
        if is_correct:
            correct_count += 1
        else:
            incorrect_count += 1
        
        results.append({
            'question': question,
            'selected_answers': selected_answers,
            'correct_answers': correct_answers,
            'is_correct': is_correct,
        })
    
    # Calculate total questions
    total_questions = len(results)
    
    # Check if certificate was generated
    certificate = None
    if attempt.passed:
        progress = CourseProgress.objects.filter(
            user=request.user,
            course=attempt.quiz.course
        ).first()
        
        if progress and progress.is_completed:
            certificate = Certificate.objects.filter(
                user=request.user,
                course=attempt.quiz.course
            ).first()
    
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'course': attempt.quiz.course,
        'results': results,
        'certificate': certificate,
        # Add these for the stats
        'total_questions': total_questions,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
    }
    
    return render(request, 'lms/quiz_result.html', context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .models import Video, CourseProgress, Certificate

# views.py


from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404
import json
from .models import Video, CourseProgress, Certificate

@login_required
@require_POST
def mark_video_complete(request, video_id):
    """Mark a video as completed and update progress"""
    try:
        video = get_object_or_404(Video, id=video_id)
        course = video.curriculum_day.course
        
        # Get or create UserVideoProgress
        progress, created = UserVideoProgress.objects.get_or_create(
            user=request.user,
            video=video,
            defaults={
                'is_completed': False,
                'watched_percentage': 0,
                'watched_duration': 0
            }
        )
        
        # Parse request body
        try:
            data = json.loads(request.body)
            watched_percentage = data.get('progress_percentage', 100)
        except:
            watched_percentage = 100
        
        # Update video progress
        progress.is_completed = True
        progress.watched_percentage = watched_percentage
        progress.save()
        
        # Get or create CourseProgress (for quiz tracking)
        course_progress, created = CourseProgress.objects.get_or_create(
            user=request.user,
            course=course
        )
        
        # Add video to completed videos
        if video not in course_progress.completed_videos.all():
            course_progress.completed_videos.add(video)
        
        # Update course progress
        course_progress.update_progress()
        
        # Check if all videos are completed
        all_videos = Video.objects.filter(curriculum_day__course=course)
        total_videos = all_videos.count()
        completed_videos = UserVideoProgress.objects.filter(
            user=request.user,
            video__in=all_videos,
            is_completed=True
        ).count()
        
        all_videos_completed = (completed_videos == total_videos)
        
        # Check if course is fully completed (videos + quiz)
        course_completed = course_progress.check_completion()
        
        # Get certificate if generated
        certificate = None
        if course_completed:
            try:
                from .models import Certificate
                certificate = Certificate.objects.get(
                    user=request.user,
                    course=course
                )
            except Certificate.DoesNotExist:
                certificate = None
        
        # Check if course has quiz
        has_quiz = False
        try:
            has_quiz = hasattr(course, 'quiz') and course.quiz is not None
        except:
            has_quiz = False
        
        return JsonResponse({
            'success': True,
            'status': 'success',
            'progress_percentage': float(course_progress.progress_percentage),
            'all_videos_completed': all_videos_completed,
            'quiz_passed': course_progress.quiz_passed,
            'quiz_required': has_quiz,
            'course_completed': course_completed,
            'certificate_id': certificate.certificate_id if certificate else None,
            'message': 'Video marked as complete'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'status': 'error',
            'error': str(e),
            'message': f'Error marking video complete: {str(e)}'
        }, status=400)

@login_required
def my_achievements(request):
    """Optimized version for better performance with large datasets"""
    from django.db.models import Prefetch, Count
    
    user = request.user
    
    # 1. Get certificates with optimized query
    certificates = Certificate.objects.filter(
        user=user
    ).select_related('course').only(
        'certificate_id', 'issue_date', 'quiz_score',
        'course__title', 'course__slug', 'course__thumbnail'
    ).order_by('-issue_date')
    
    # 2. Get progress with aggregated data
    from django.db.models import Count, Case, When, IntegerField, FloatField
    
    # Get all courses the user has purchased
    purchased_course_ids = Purchase.objects.filter(
        user=user,
        payment_status='completed'
    ).values_list('course_id', flat=True)
    
    purchased_courses = Course.objects.filter(
        id__in=purchased_course_ids
    ).prefetch_related(
        Prefetch(
            'curriculum_days__videos',
            queryset=Video.objects.only('id')
        )
    ).only('id', 'title', 'slug', 'thumbnail')
    
    # 3. Get course progress efficiently
    progress_queryset = CourseProgress.objects.filter(
        user=user,
        course__in=purchased_courses
    ).select_related('course').only(
        'course__title', 'progress_percentage', 
        'is_completed', 'quiz_passed', 'last_quiz_attempt_id'
    ).annotate(
        completed_videos_count=Count('completed_videos')
    )
    
    # 4. Calculate statistics in bulk
    total_courses = purchased_courses.count()
    completed_courses = certificates.values('course').distinct().count()
    
    # Alternative: Count from progress
    completed_from_progress = progress_queryset.filter(is_completed=True).count()
    completed_courses = max(completed_courses, completed_from_progress)
    
    in_progress_courses = total_courses - completed_courses
    
    # 5. Build detailed progress list efficiently
    detailed_progress = []
    
    # Create a dictionary for quick lookup
    progress_dict = {p.course_id: p for p in progress_queryset}
    
    for course in purchased_courses:
        progress = progress_dict.get(course.id)
        
        if progress:
            # Get total videos count from prefetched data
            total_videos = sum(day.videos.count() for day in course.curriculum_days.all())
            
            # Calculate actual percentage
            if total_videos > 0:
                completed_videos = progress.completed_videos_count
                actual_percentage = (completed_videos / total_videos) * 100
            else:
                actual_percentage = progress.progress_percentage
            
            detailed_progress.append({
                'course': course,
                'progress_percentage': round(actual_percentage, 1),
                'is_completed': progress.is_completed,
                'quiz_passed': progress.quiz_passed,
                'completed_videos_count': progress.completed_videos_count,
                'total_videos': total_videos,
                'has_certificate': certificates.filter(course=course).exists(),
            })
    
    # 6. Sort progress
    detailed_progress.sort(
        key=lambda x: (
            not x['is_completed'],  # Completed first
            -x['progress_percentage']  # Higher percentage first
        )
    )
    
    context = {
        'certificates': certificates[:10],  # Limit for display
        'progress_data': detailed_progress,
        'completed_courses': completed_courses,
        'in_progress_courses': max(0, in_progress_courses),
        'total_courses': total_courses,
        'user': user,
    }
    
    return render(request, 'lms/achievements.html', context)




from PIL import Image, ImageDraw, ImageFont
from django.conf import settings
import os


@login_required
def certificate_detail(request, certificate_id):
    """Display individual certificate"""
    certificate = get_object_or_404(
        Certificate, 
        certificate_id=certificate_id, 
        user=request.user
    )
    
    # Generate certificate image dynamically
    try:
        certificate.generated_image = cert_image_path
        certificate.save()
    except Exception as e:
        # Log error but continue - will show template without generated image
        print(f"Error generating certificate: {e}")
        cert_image_path = None
    
    context = {
        'certificate': certificate,
        'cert_image_path': cert_image_path,
    }
    return render(request, 'lms/certificate_detail.html', context)


@login_required
def download_certificate(request, certificate_id):
    """Download certificate as PDF"""
    from django.template.loader import render_to_string
    from django.http import HttpResponse
    
    certificate = get_object_or_404(
        Certificate, 
        certificate_id=certificate_id, 
        user=request.user
    )
    
    # For now, render HTML version
    # You can integrate libraries like reportlab or weasyprint for PDF
    html = render_to_string('lms/certificate_pdf.html', {'certificate': certificate})
    return HttpResponse(html, content_type='text/html')
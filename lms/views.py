from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from .models import User, HeroSection, Category, Course, Enrollment, Lesson
from .models import FeatureSection, HomeAboutSection, CourseCategory, CourseReview, Payment
import razorpay
import json
import uuid
from django.contrib.auth import get_user_model

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
    featured_courses = Course.objects.filter(is_active=True, is_featured=True).order_by('order')[:8]
    
    if featured_courses.count() < 8:
        additional_courses = Course.objects.filter(
            is_active=True
        ).exclude(
            id__in=[c.id for c in featured_courses]
        ).order_by('order')[:8 - featured_courses.count()]
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
    }
    return render(request, 'lms/home.html', context)

from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, get_user_model

User = get_user_model()

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
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # ✅ Login without specifying backend now works
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next')
            return redirect(next_url or 'home')
        else:
            messages.error(request, 'Invalid email or password!')
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
                username=email,  # username required
                email=email,
                password=password,
                first_name=name
            )
            # ✅ Automatically login after signup
            login(request, user)
            messages.success(request, f'Welcome {name}! Account created successfully!')
            return redirect('home')
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
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
    courses = Course.objects.filter(is_active=True).order_by('order')
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
    courses = Course.objects.filter(category=category, is_active=True).order_by('order')
    all_categories = CourseCategory.objects.filter(is_active=True).order_by('order')
    
    context = {
        'category': category,
        'courses': courses,
        'categories': all_categories,
        'selected_category': category_slug,
    }
    return render(request, 'courses/category.html', context)

def course_detail(request, slug):
    """View for individual course detail page"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    related_courses = Course.objects.filter(
        category=course.category,
        is_active=True
    ).exclude(
        id=course.id
    ).order_by('order')[:4]
    
    context = {
        'course': course,
        'related_courses': related_courses
    }
    return render(request, 'courses/detail.html', context)

def my_courses(request):
    """Simple view for my courses page"""
    context = {
        'title': 'My Courses',
        'message': 'This is where users will see their enrolled courses.'
    }
    return render(request, 'lms/my_courses.html', context)

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
    return placeholder_view(request, 'about')

def enroll_course(request, slug):
    """Simple enrollment view"""
    course = get_object_or_404(Course, slug=slug, is_active=True)
    
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to enroll in this course.')
        return redirect('login') + f'?next={request.path}'
    
    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, f'You are already enrolled in "{course.title}"')
        return redirect('course_detail', slug=slug)
    
    if request.method == 'POST':
        Enrollment.objects.create(user=request.user, course=course)
        messages.success(request, f'Successfully enrolled in "{course.title}"!')
        return redirect('my_courses')
    
    context = {
        'course': course,
    }
    return render(request, 'courses/enroll.html', context)

# ===== PAYMENT VIEWS =====
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
import uuid
import razorpay

from .models import Course, Enrollment, Payment


# Razorpay client (define ONCE)
razorpay_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)
@login_required
def checkout(request, slug):
    course = get_object_or_404(Course, slug=slug, is_active=True)

    if Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, f'You are already enrolled in "{course.title}"')
        return redirect('course_detail', slug=slug)

    # Base price
    base_price = course.discount_price if course.is_on_discount and course.discount_price else course.price

    base_price = float(base_price)

    tax_rate = 0.18
    tax_amount = round(base_price * tax_rate, 2)
    total_amount = round(base_price + tax_amount, 2)

    amount_paise = int(total_amount * 100)

    order = razorpay_client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'payment_capture': '1',
    })

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
        
        Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'enrolled_date': timezone.now()}
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
        
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return JsonResponse({
                'success': False,
                'error': 'Already enrolled in this course'
            }, status=400)
        
        if course.is_on_discount and course.discount_price:
            amount = float(course.discount_price)
        else:
            amount = float(course.price)
        
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
        
        if Enrollment.objects.filter(user=request.user, course=course).exists():
            return JsonResponse({
                'success': False,
                'error': 'Already enrolled in this course'
            }, status=400)
        
        test_order_id = f'test_order_{uuid.uuid4().hex[:10]}'
        test_payment_id = f'test_payment_{uuid.uuid4().hex[:10]}'
        
        amount = float(course.discount_price if course.is_on_discount and course.discount_price else course.price)
        
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
        
        Enrollment.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'enrolled_date': timezone.now()}
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
    
    # In views.py - add this function if it doesn't exist
def about_us(request):
    """About Us page"""
    return render(request, 'lms/about.html', {
        'title': 'About Us',
        'message': 'Learn more about our e-learning platform.'
    })

def contact_us(request):
    return render(request, "lms/contact.html")

def privacy_policy(request):
    return render(request, "privacy_policy.html")

def terms_of_use(request):
    return render(request, "terms_of_use.html")



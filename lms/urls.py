# lms/urls.py
from django.urls import path
from . import views





urlpatterns = [
    # Authentication
    path('', views.home, name='home'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Course pages
    path('courses/', views.all_courses, name='all_courses'),
    path('courses/category/<slug:category_slug>/', views.courses_by_category, name='courses_by_category'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    # lms/urls.py - add this
    path('courses/<slug:slug>/initiate-purchase/', views.initiate_purchase, name='initiate_purchase'),
    path('my-courses/', views.my_courses, name='my_courses'),
    path("courses/<slug:slug>/checkout/", views.checkout, name="checkout"),


    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/failed/", views.payment_failed, name="payment_failed"),
    
    # Payment
    path('checkout/<slug:slug>/', views.checkout, name='checkout'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    
    # Optional payment URLs (comment out if not needed)
    # path('create-order/<slug:slug>/', views.create_razorpay_order, name='create_razorpay_order'),
    # path('test-payment/<slug:slug>/', views.create_test_payment, name='create_test_payment'),
    # path('webhook/', views.razorpay_webhook, name='razorpay_webhook'),
    
    # Other pages - MAKE SURE THESE ARE CORRECT
    path("about/", views.about_us, name="about_us"),  # Changed from 'about_us' to 'about'
    path('contact/', views.contact_view, name='contact'),
    path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    path("terms-of-use/", views.terms_of_use, name="terms_of_use"),
    path('enroll/<slug:slug>/', views.enroll_course, name='enroll_course'),
    
    # Placeholder pages
    path('contact/', views.placeholder_view, {'page_name': 'contact'}, name='contact'),
    path('privacy/', views.placeholder_view, {'page_name': 'privacy'}, name='privacy'),
    path('terms/', views.placeholder_view, {'page_name': 'terms'}, name='terms'),

   # Purchase URLs
   
    path('payment/<int:purchase_id>/', views.payment_page, name='payment_page'),
    path('payment/<int:purchase_id>/complete/', views.complete_payment, name='complete_payment'),
    path('payment/callback/', views.razorpay_callback, name='razorpay-callback'),
    
    # Video URLs
    path('video/<int:video_id>/', views.video_player, name='video_player'),
    path('video/<int:video_id>/complete/', views.mark_video_complete, name='mark_video_complete'),
    path('video/<int:video_id>/progress/', views.update_video_progress, name='update_video_progress'),
    path('video/<int:video_id>/', views.video_player, name='video_player'),
   

      path('enroll/<slug:slug>/', views.enroll_course, name='enroll_course'),
    
    # My Courses
    path('my-courses/', views.my_courses, name='my_courses'),


    path('course/<slug:course_slug>/quiz/', views.quiz_start, name='quiz_start'),
    path('course/<slug:course_slug>/quiz/take/', views.quiz_take, name='quiz_take'),
    path('quiz/attempt/<int:attempt_id>/submit/', views.quiz_submit, name='quiz_submit'),
    path('quiz/attempt/<int:attempt_id>/result/', views.quiz_result, name='quiz_result'),
    
    # Achievement and Certificate URLs
    
    path('achievements/', views.my_achievements, name='my_achievements'),
    path('certificate/<str:certificate_id>/', views.certificate_detail, name='certificate_detail'),
    path('certificate/<str:certificate_id>/download/', views.download_certificate, name='download_certificate'),
    
    
]
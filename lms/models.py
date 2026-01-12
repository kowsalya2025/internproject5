from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        related_name='lms_user_set',
        related_query_name='lms_user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        related_name='lms_user_set',
        related_query_name='lms_user',
    )
    
    def __str__(self):
        return self.email

class HeroSection(models.Model):
    title_primary = models.CharField(max_length=200)
    title_secondary = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=200, blank=True)

    button_text = models.CharField(max_length=50, default="Enroll Now")
    hero_image = models.ImageField(upload_to='hero/', blank=True)
    background_color = models.CharField(max_length=7, default="#1abc9c")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        verbose_name = "Hero Section"
        verbose_name_plural = "Hero Sections"
    
    def __str__(self):
     return self.title_primary
    
from django.db import models

# ================= FEATURE SECTION TITLE =================
class FeatureSection(models.Model):
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


# ================= FEATURE CARDS =================
class FeatureItem(models.Model):
    section = models.ForeignKey(
        FeatureSection,
        on_delete=models.CASCADE,
        related_name='items'
    )
    number = models.CharField(max_length=2)   # 01, 02, 03, 04
    heading = models.CharField(max_length=100)
    description = models.TextField()
    

    def __str__(self):
        return f"{self.number} - {self.heading}"


from django.db import models
from ckeditor.fields import RichTextField

class HomeAboutSection(models.Model):
    title = models.CharField(max_length=200, default="About Our Platform")
    subtitle = models.CharField(max_length=300, default="We are innovative educational institution to the creation of the student")
    description = RichTextField(blank=True, null=True)
    button_text = models.CharField(max_length=100, default="Browse All Courses")
    button_link = models.CharField(max_length=200, default="/courses/")
    image = models.ImageField(upload_to='home/about/', null=True, blank=True, verbose_name="About Section Image")
    
    # Team section fields
    team_title = models.CharField(max_length=200, default="Our Team")
    team_description = models.TextField(default="Our team consists of certified IT professionals with expertise in network security, cloud computing, software development, and technical support. With decades of combined experience, we provide strategic IT guidance and technical support tailored to your business needs.")
    
    # Settings
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Home About Section"
        verbose_name_plural = "Home About Sections"

class Category(models.Model):
    name = models.CharField(max_length=100)
    icon = models.ImageField(upload_to='categories/')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order']
    
    def __str__(self):
        return self.name
    

# models.py
from django.db import models
from ckeditor.fields import RichTextField
from django.urls import reverse
from django.conf import settings  # Add this import

# Use settings.AUTH_USER_MODEL instead of User

class CourseCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class, e.g., 'fas fa-paint-brush'")
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        verbose_name = "Course Category"
        verbose_name_plural = "Course Categories"
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Instructor(models.Model):
    """Model for course instructors"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # Changed from User
        on_delete=models.CASCADE, 
        blank=True, 
        null=True
    )
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=200, blank=True, help_text="e.g., 'Senior Developer', 'Data Scientist'")
    bio = RichTextField(blank=True)
    photo = models.ImageField(upload_to='instructors/', blank=True, null=True)
    email = models.EmailField(blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    website_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name

class Course(models.Model):
    # Course details
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    short_description = models.TextField(max_length=200)
    full_description = RichTextField()
    
    # Category
    category = models.ForeignKey(CourseCategory, on_delete=models.CASCADE, related_name='courses')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Course details
    duration = models.CharField(max_length=100, blank=True, help_text="e.g., '3 months', '40 hours'")
    level = models.CharField(max_length=50, choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('all', 'All Levels')
    ], default='beginner')
    
    # Image
    thumbnail = models.ImageField(upload_to='courses/thumbnails/', blank=True, null=True)
    
    # NEW FIELDS FOR DETAIL PAGE
    tagline = models.TextField(max_length=300, blank=True, 
                              help_text="Short catchy tagline shown below course title")
    instructors = models.CharField(max_length=300, blank=True, 
                                  help_text="Instructor names, comma separated (e.g., 'Saran, Deepan')")
    instructor = models.ForeignKey(
        Instructor, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='courses',
        help_text="Main instructor for this course"
    )
    preview_video_url = models.URLField(blank=True, 
                                       help_text="YouTube/Vimeo embed URL for course preview")
    total_videos = models.IntegerField(default=0, help_text="Total number of video lessons")
    total_projects = models.IntegerField(default=0, help_text="Number of projects included")
    total_resources = models.IntegerField(default=0, help_text="Number of downloadable resources")
    learning_outcomes = RichTextField(blank=True, 
                                     help_text="What students will learn (use bullet points)")
    prerequisites = RichTextField(blank=True, 
                                 help_text="Requirements before taking this course")
    
    # Navigation
    page_url = models.CharField(max_length=200, blank=True, help_text="URL to course detail page. Leave blank to use auto-generated slug URL")
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        if self.page_url:
            return self.page_url
        return reverse('course_detail', kwargs={'slug': self.slug})
    
    @property
    def is_on_discount(self):
        """Check if course has discount"""
        return bool(self.discount_price and self.discount_price < self.price)
    
    @property
    def discount_amount(self):
        """Calculate discount amount"""
        if self.is_on_discount and self.discount_price:
            return self.price - self.discount_price
        return 0
    
    @property
    def get_display_price(self):
        """Get current display price"""
        if self.is_free:
            return "Free"
        if self.is_on_discount and self.discount_price:
            return f"${self.discount_price}"
        return f"${self.price}"
    
    @property
    def get_original_price(self):
        """Get original price for display"""
        if self.is_free:
            return None
        if self.is_on_discount:
            return f"${self.price}"
        return None

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    duration = models.CharField(max_length=20)
    
    # For curriculum organization
    module_title = models.CharField(max_length=200, blank=True, 
                                   help_text="Module/section title for grouping")
    is_preview = models.BooleanField(default=False, 
                                     help_text="Mark if this lesson is free preview")
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"

class CourseReview(models.Model):
    """Model for course reviews/ratings"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Changed from User
        on_delete=models.CASCADE
    )
    rating = models.IntegerField(choices=[
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars')
    ], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} ({self.rating} stars)"

class Enrollment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Changed from User
        on_delete=models.CASCADE
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    completed = models.BooleanField(default=False)
    progress = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ['user', 'course']
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
    
    # models.py
import uuid
from django.db import models

# models.py
class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ], default='pending')
    
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    
    # Billing Information
    billing_first_name = models.CharField(max_length=100, blank=True, null=True)
    billing_last_name = models.CharField(max_length=100, blank=True, null=True)
    billing_email = models.EmailField(blank=True, null=True)
    billing_phone = models.CharField(max_length=20, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    billing_city = models.CharField(max_length=100, blank=True, null=True)
    billing_state = models.CharField(max_length=100, blank=True, null=True)
    billing_zip_code = models.CharField(max_length=20, blank=True, null=True)
    billing_country = models.CharField(max_length=100, default='IN')
    
    notes = models.TextField(blank=True, null=True)
    
    payment_date = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.course.title} - {self.amount}"
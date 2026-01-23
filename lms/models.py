from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings
from ckeditor.fields import RichTextField
from django.utils import timezone
import uuid

from urllib3 import request


# ============================
# USER MANAGER
# ============================
class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


# ============================
# CUSTOM USER MODEL
# ============================
class User(AbstractUser):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, unique=True, blank=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['username']
    
    objects = UserManager()

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        # Auto-generate username from email if not set
        if not self.username and self.email:
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)


# ============================
# HERO SECTION
# ============================
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


# ============================
# FEATURE SECTION
# ============================
class FeatureSection(models.Model):
    title = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class FeatureItem(models.Model):
    section = models.ForeignKey(
        FeatureSection, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    number = models.CharField(max_length=2)  # 01, 02, 03, 04
    heading = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"{self.number} - {self.heading}"


# ============================
# HOME ABOUT SECTION
# ============================
class HomeAboutSection(models.Model):
    title = models.CharField(max_length=200, default="About Our Platform")
    subtitle = models.CharField(max_length=300, default="We are innovative educational institution to the creation of the student")
    description = RichTextField(blank=True, null=True)
    button_text = models.CharField(max_length=100, default="Browse All Courses")
    button_link = models.CharField(max_length=200, default="/courses/")
    image = models.ImageField(upload_to='home/about/', null=True, blank=True, verbose_name="About Section Image")
    
    # Team section fields
    team_title = models.CharField(max_length=200, default="Our Team")
    team_description = models.TextField(default="Our team consists of certified IT professionals with expertise in network security, cloud computing, software development, and technical support.")
    
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


# ============================
# CATEGORY
# ============================
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


# ============================
# COURSE CATEGORY
# ============================
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


# ============================
# INSTRUCTOR
# ============================
class Instructor(models.Model):
    """Model for course instructors"""
    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=150)  # NEW FIELD
    profile_image = models.ImageField(upload_to='instructors/', blank=True, null=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Instructor"
        verbose_name_plural = "Instructors"



# ============================
# COURSE
# ============================
from django.db import models
from django.urls import reverse
from ckeditor.fields import RichTextField


class Course(models.Model):
    # =========================
    # CORE IDENTITY
    # =========================
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    short_description = models.CharField(
        max_length=300,
        help_text="Short summary shown in course cards"
    )
    description = RichTextField(
        help_text="Full course description"
    )

    tagline = models.CharField(
        max_length=300,
        blank=True,
        help_text="Catchy line below course title"
    )

    # =========================
    # RELATIONS
    # =========================
    category = models.ForeignKey(
        CourseCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses'
    )

    instructors = models.ManyToManyField(
        Instructor,
        related_name='courses'
    )

    # =========================
    # PRICING
    # =========================
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    discounted_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    is_free = models.BooleanField(default=False)

    # =========================
    # COURSE METADATA
    # =========================
    duration_hours = models.PositiveIntegerField(
        help_text="Total course duration in hours"
    )

    total_videos = models.PositiveIntegerField(default=0)
    total_projects = models.PositiveIntegerField(default=0)
    total_resources = models.PositiveIntegerField(default=0)

    languages = models.CharField(
        max_length=200,
        default="Tamil, English"
    )
    total_learners = models.CharField(max_length=50)
    payment_type = models.CharField(max_length=50)

    level = models.CharField(
        max_length=50,
        choices=[
            ('beginner', 'Beginner'),
            ('intermediate', 'Intermediate'),
            ('advanced', 'Advanced'),
            ('all', 'All Levels'),
        ],
        default='beginner'
    )

    access_level = models.CharField(
        max_length=100,
        default="Anyone Can Learn (IT / Non-IT)"
    )

    # =========================
    # CONTENT
    # =========================
    learning_outcomes = RichTextField(blank=True)
    prerequisites = RichTextField(blank=True)

    skills = models.TextField(
        help_text="Comma-separated skills (e.g., Python, Django, React, HTML, CSS)"
    )

    tools_learned = models.TextField(
        help_text="Comma-separated tools (e.g., VSCode, GitHub, Figma, Docker)"
    )

    certification_details = models.TextField(blank=True)

    # =========================
    # MEDIA
    # =========================
    thumbnail = models.ImageField(
        upload_to='courses/thumbnails/',
        blank=True,
        null=True
    )

    preview_video_url = models.URLField(blank=True)

    # =========================
    # STATUS
    # =========================
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # =========================
    # ICON MAPPINGS (CLASS ATTRIBUTES)
    # =========================
    SKILL_ICON_MAP = {
        'python': 'fab fa-python',
        'django': 'fab fa-python',
        'flask': 'fas fa-flask',
        'react': 'fab fa-react',
        'javascript': 'fab fa-js-square',
        'html': 'fab fa-html5',
        'css': 'fab fa-css3-alt',
        'git': 'fab fa-git-alt',
        'github': 'fab fa-github',
        'docker': 'fab fa-docker',
        'aws': 'fab fa-aws',
        'database': 'fas fa-database',
        'sql': 'fas fa-database',
        'mongodb': 'fas fa-database',
        'rest api': 'fas fa-code',
        'testing': 'fas fa-vial',
        'security': 'fas fa-shield-alt',
        'devops': 'fas fa-server',
        'ui': 'fas fa-paint-brush',
        'ux': 'fas fa-user-friends',
        'figma': 'fab fa-figma',
        # Add more as needed
    }

    TOOL_ICON_MAP = {
        'vscode': 'fas fa-code',
        'visual studio code': 'fas fa-code',
        'github': 'fab fa-github',
        'git': 'fab fa-git-alt',
        'postman': 'fas fa-code',
        'docker': 'fab fa-docker',
        'jenkins': 'fas fa-cog',
        'aws': 'fab fa-aws',
        'figma': 'fab fa-figma',
        'notion': 'fas fa-sticky-note',
        'jira': 'fab fa-jira',
        'slack': 'fab fa-slack',
        # Add more as needed
    }

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Course"
        verbose_name_plural = "Courses"

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('course_detail', kwargs={'slug': self.slug})

    # =========================
    # HELPERS
    # =========================
    def get_discount_percentage(self):
        if self.discounted_price and self.original_price:
            return int(
                ((self.original_price - self.discounted_price)
                 / self.original_price) * 100
            )
        return 0

    def get_skills_list(self):
        return [s.strip() for s in self.skills.split(',') if s.strip()]

    def get_tools_list(self):
        return [t.strip() for t in self.tools_learned.split(',') if t.strip()]

    # =========================
    # NEW ICON METHODS
    # =========================
    def get_skill_icon(self, skill_name):
        """Get icon for a specific skill"""
        skill_lower = skill_name.lower().strip()
        return self.SKILL_ICON_MAP.get(skill_lower, 'fas fa-code')

    def get_tool_icon(self, tool_name):
        """Get icon for a specific tool"""
        tool_lower = tool_name.lower().strip()
        return self.TOOL_ICON_MAP.get(tool_lower, 'fas fa-toolbox')

    def get_skills_with_icons(self):
        """Return list of skills with their icons"""
        skills_list = self.get_skills_list()
        return [
            {
                'name': skill,
                'icon': self.get_skill_icon(skill)
            }
            for skill in skills_list
        ]

    def get_tools_with_icons(self):
        """Return list of tools with their icons"""
        tools_list = self.get_tools_list()
        return [
            {
                'name': tool,
                'icon': self.get_tool_icon(tool)
            }
            for tool in tools_list
        ]



# ============================
# COURSE TOOL (Legacy - for backward compatibility)
# ============================
class CourseTool(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tools')
    tool_name = models.CharField(max_length=100)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.course.title} - {self.tool_name}"


# ============================
# CURRICULUM DAY
# ============================
class CurriculumDay(models.Model):
    """Model for organizing course curriculum by days"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='curriculum_days')
    day_number = models.IntegerField()
    title = models.CharField(max_length=200, blank=True, help_text="Optional day title")
    description = models.TextField(blank=True)
    is_free = models.BooleanField(default=False, help_text="Make this day free for all users")
    order = models.IntegerField(default=0, help_text="Display order")
    
    def __str__(self):
        return f"{self.course.title} - Day {self.day_number:02d}"
    
    class Meta:
        verbose_name = "Curriculum Day"
        verbose_name_plural = "Curriculum Days"
        ordering = ['order', 'day_number']
        unique_together = ['course', 'day_number']




# ============================
# VIDEO
# ============================
from django.db import models
from django.conf import settings
from .models import CurriculumDay  # Make sure Purchase and CurriculumDay are imported

class Video(models.Model):
    """Model for course videos"""
    curriculum_day = models.ForeignKey(
        CurriculumDay, 
        on_delete=models.CASCADE, 
        related_name='videos'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    video_url = models.URLField(help_text="URL to video file or embed link")
    video_file = models.FileField(upload_to='course_videos/', blank=True, null=True)
    duration = models.CharField(max_length=10, help_text="Format: MM:SS or HH:MM:SS")
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    order = models.IntegerField(default=0)
    is_free = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.curriculum_day} - {self.title}"

    # -----------------------------
    # Video URL helpers
    # -----------------------------
    def get_youtube_id(self):
        """Extract YouTube video ID from URL"""
        if not self.video_url:
            return None
        
        import re
        from urllib.parse import urlsplit, parse_qs

        url = str(self.video_url).strip()
        patterns = [
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([\w\-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([\w\-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([\w\-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([\w\-]{11})',
            r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/shorts\/([\w\-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                video_id = match.group(1)
                if len(video_id) == 11 and re.match(r'^[\w\-]+$', video_id):
                    return video_id
        
        # Fallback parsing
        try:
            parsed = urlsplit(url)
            if parsed.netloc in ['youtu.be', 'www.youtu.be']:
                video_id = parsed.path.strip('/').split('?')[0]
                if len(video_id) == 11:
                    return video_id
            if 'youtube.com' in parsed.netloc:
                if parsed.path.startswith('/watch'):
                    query_params = parse_qs(parsed.query)
                    if 'v' in query_params:
                        video_id = query_params['v'][0]
                        if len(video_id) == 11:
                            return video_id
                elif parsed.path.startswith(('/embed/', '/v/', '/shorts/')):
                    video_id = parsed.path.split('/')[2]
                    if len(video_id) == 11:
                        return video_id
        except Exception:
            pass
        
        return None

    def get_vimeo_id(self):
        """Extract Vimeo video ID from URL"""
        if not self.video_url:
            return None
        
        import re
        match = re.search(r'vimeo\.com\/(\d+)', self.video_url)
        if match:
            return match.group(1)
        return None

    def get_embed_url(self):
        """Get embed URL for the video"""
        youtube_id = self.get_youtube_id()
        if youtube_id:
            return f"https://www.youtube.com/embed/{youtube_id}"
        
        vimeo_id = self.get_vimeo_id()
        if vimeo_id:
            return f"https://player.vimeo.com/video/{vimeo_id}"
        
        return self.video_url

    # -----------------------------
    # Access control
    # -----------------------------
    def is_accessible_by(self, user):
        from .models import Purchase
        """
        Access rules:
        - Day 1 videos are free for everyone
        - Day 2+ videos require purchase
        - Free videos are always accessible
        """
        # Free video or free curriculum day
        if self.is_free or self.curriculum_day.is_free:
            return True

        # Day 1 is free for all users
        if self.curriculum_day.day_number == 1:
            return True

        # Day 2+ requires purchase
        if user.is_authenticated:
            return Purchase.objects.filter(
                user=user,
                course=self.curriculum_day.course,
                payment_status='completed'
            ).exists()

        # Not logged in and Day 2+
        return False
   
    @property
    def youtube_id(self):
        """Property to access YouTube ID easily in templates"""
        return self.get_youtube_id()
    
    @property 
    def vimeo_id(self):
        """Property to access Vimeo ID easily in templates"""
        return self.get_vimeo_id()
    
    @property
    def is_youtube_video(self):
        """Check if this is a YouTube video"""
        return bool(self.get_youtube_id())
    
    @property
    def is_vimeo_video(self):
        """Check if this is a Vimeo video"""
        return bool(self.get_vimeo_id())
    
    @property
    def embed_url(self):
        """Get embed URL property"""
        return self.get_embed_url()

    class Meta:
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ['order', 'id']






# ============================
# LESSON (Legacy)
# ============================
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    video_url = models.URLField(blank=True)
    order = models.IntegerField(default=0)
    duration = models.CharField(max_length=20)
    module_title = models.CharField(max_length=200, blank=True, help_text="Module/section title for grouping")
    is_preview = models.BooleanField(default=False, help_text="Mark if this lesson is free preview")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# ============================
# PURCHASE
# ============================
class Purchase(models.Model):
    """Model for tracking course purchases"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='purchases')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=200, blank=True)
    purchased_at = models.DateTimeField(default=timezone.now)
    
    # User details at time of purchase
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
    
    class Meta:
        verbose_name = "Purchase"
        verbose_name_plural = "Purchases"
        ordering = ['-purchased_at']
        unique_together = ['user', 'course']





# ============================
from django.core.validators import MinValueValidator, MaxValueValidator
class UserVideoProgress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='video_progress'
    )
    video = models.ForeignKey(
        Video,
        on_delete=models.CASCADE,
        related_name='user_progress'
    )
    watched_duration = models.PositiveIntegerField(default=0)
    watched_percentage = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    is_completed = models.BooleanField(default=False)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'video')
        verbose_name = "User Video Progress"
        verbose_name_plural = "User Video Progress"

    def save(self, *args, **kwargs):
        """Update watched_percentage before saving"""
        if self.video and self.video.duration:
            try:
                # Calculate percentage
                video_duration = float(self.video.duration)
                if video_duration > 0:
                    percentage = (float(self.watched_duration) / video_duration) * 100
                    # Cap at 100%
                    self.watched_percentage = min(percentage, 100)
                    
                    # Auto-mark as completed if watched >= 95%
                    if not self.is_completed and self.watched_percentage >= 95:
                        self.is_completed = True
            except (ValueError, TypeError):
                # Keep existing percentage if calculation fails
                pass
        
        super().save(*args, **kwargs)
    
    @property
    def progress_percentage(self):
        """Alias for watched_percentage for backward compatibility"""
        return self.watched_percentage
    
    @property
    def progress_percentage_display(self):
        """Formatted percentage for display"""
        return f"{self.watched_percentage:.1f}%"

    def __str__(self):
        return f"{self.user.email} - {self.video.title} ({self.watched_percentage}%)"



# models.py - Update your existing CourseReview model

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class CourseReview(models.Model):
    """Student reviews for courses"""
    course = models.ForeignKey(
        'Course', 
        on_delete=models.CASCADE, 
        related_name='course_reviews'  # Changed from 'reviews' to avoid clash
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Fixed: Use settings.AUTH_USER_MODEL instead of User
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='given_reviews'
    )
    name = models.CharField(max_length=100)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    review = models.TextField()
    photo = models.ImageField(
        upload_to='reviews/', 
        null=True, 
        blank=True,
        help_text="Optional profile photo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Course Review'
        verbose_name_plural = 'Course Reviews'

    def __str__(self):
        return f"{self.name} - {self.course.title} ({self.rating}★)"

    @property
    def get_photo_url(self):
        """Return photo URL or default avatar"""
        if self.photo:
            return self.photo.url
        # Return default avatar
        return f"https://ui-avatars.com/api/?name={self.name.replace(' ', '+')}&background=10b981&color=fff"


# ============================
# COURSE ENROLLMENT
# ============================
class CourseEnrollment(models.Model):
    ENROLLMENT_STATUS = [
        ('free', 'Free Enrollment'),
        ('paid', 'Paid Enrollment'),
        ('trial', 'Trial Period'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_type = models.CharField(max_length=20, choices=ENROLLMENT_STATUS, default='free')
    is_paid = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        unique_together = ['user', 'course']
        verbose_name = "Course Enrollment"
        verbose_name_plural = "Course Enrollments"

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"

    def has_access(self):
        """Check if user still has access to the course"""
        if self.is_paid:
            if self.expires_at:
                return timezone.now() < self.expires_at
            return True
        return self.enrollment_type in ['free', 'trial']


# ============================
# PAYMENT
# ============================
class Payment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded')
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='payments')
    razorpay_order_id = models.CharField(max_length=100, unique=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='INR')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
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
        return f"{self.user.email} - {self.course.title} - ₹{self.amount}"
    


# home page
from django.db import models

class HomeBanner(models.Model):
    """Model for Home Page Banner Section"""
    title = models.CharField(max_length=200, default="Join World's largest learning platform today")
    highlight_text = models.CharField(max_length=50, default="World's largest")
    subtitle = models.CharField(max_length=200, default="Start learning by registering for free")
    button_text = models.CharField(max_length=50, default="Sign up for Free")
    button_url = models.CharField(max_length=200, help_text="Enter a relative URL like /signup/")
    image = models.ImageField(upload_to='home_banner/')
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=1, help_text="Order of display if multiple banners exist")

    class Meta:
        verbose_name = "Home Page Banner"
        verbose_name_plural = "Home Page Banners"
        ordering = ['order']

    def __str__(self):
        return self.title


from django.db import models

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=150)
    message = models.TextField()
    profile_image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    

    from django.db import models

class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.question

from django.db import models

class ContactMessage(models.Model):
    SUBJECT_CHOICES = [
        ('Course Enquiry', 'Course Enquiry'),
        ('Admission', 'Admission'),
        ('Support', 'Support'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"



# quezz
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid

class CourseProgress(models.Model):
    """Track user's progress through a course"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    completed_videos = models.ManyToManyField('Video', blank=True)
    progress_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    quiz_passed = models.BooleanField(default=False)
    last_quiz_attempt_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID of the quiz attempt that passed")
    
    
    class Meta:
        unique_together = ['user', 'course']
        verbose_name_plural = 'Course Progress'
    
    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.progress_percentage}%)"
    
    def update_progress(self):
        """Calculate and update course progress"""
        # Get total videos count through curriculum days
        total_videos = Video.objects.filter(
            curriculum_day__course=self.course
        ).count()
        
        if total_videos > 0:
            completed = self.completed_videos.count()
            self.progress_percentage = (completed / total_videos) * 100
            self.save()
    
    def has_passed_quiz_actually(self):
        """
        Check if user has actually passed the quiz with a valid attempt
        Returns True only if:
        1. quiz_passed is True
        2. last_quiz_attempt_id is set
        3. QuizAttempt exists with that ID and is passed
        """
        if not self.quiz_passed or not self.last_quiz_attempt_id:
            return False
            
        try:
            from .models import QuizAttempt  # Import here to avoid circular import
            attempt = QuizAttempt.objects.get(
                id=self.last_quiz_attempt_id,
                user=self.user,
                quiz__course=self.course,
                passed=True,
                completed_at__isnull=False  # Must be completed
            )
            return True
        except (QuizAttempt.DoesNotExist, ValueError):
            return False
    
    def check_completion(self):
        """Check if course is fully completed (all videos + quiz passed)"""
        # Get total videos count through curriculum days
        total_videos = Video.objects.filter(
            curriculum_day__course=self.course
        ).count()
        
        completed_videos = self.completed_videos.count()
        
        # Only mark as completed if:
        # 1. All videos are completed
        # 2. Quiz is actually passed (not just flagged)
        # 3. Not already marked as completed
        if total_videos > 0:
            videos_completed = completed_videos == total_videos
            quiz_actually_passed = self.has_passed_quiz_actually()
            
            if videos_completed and quiz_actually_passed and not self.is_completed:
                self.is_completed = True
                self.completed_at = timezone.now()
                self.save()
                
                # Generate certificate
                from .models import Certificate
                Certificate.objects.get_or_create(
                    user=self.user,
                    course=self.course,
                    defaults={
                        'issue_date': timezone.now(),
                        'certificate_id': uuid.uuid4().hex[:12].upper(),
                        'quiz_score': self.get_quiz_score()  # Store actual quiz score
                    }
                )
                return True
        return False
    
    def get_quiz_score(self):
        """Get the actual quiz score from the passed attempt"""
        if not self.last_quiz_attempt_id:
            return None
            
        try:
            from .models import QuizAttempt
            attempt = QuizAttempt.objects.get(id=self.last_quiz_attempt_id)
            return attempt.score
        except QuizAttempt.DoesNotExist:
            return None
    
    def mark_quiz_passed(self, quiz_attempt):
        """
        Mark quiz as passed ONLY when user actually passes a quiz attempt
        This should be called from QuizAttempt.calculate_score() only
        """
        if not quiz_attempt.passed:
            return False
            
        # Verify this is a valid completed attempt
        if not quiz_attempt.completed_at:
            return False
            
        # Verify the attempt belongs to this user and course
        if (quiz_attempt.user != self.user or 
            quiz_attempt.quiz.course != self.course):
            return False
        
        # Mark quiz as passed
        self.quiz_passed = True
        self.last_quiz_attempt_id = str(quiz_attempt.id)
        self.save()
        
        # Check if course can now be completed
        self.check_completion()
        return True
    
    def reset_quiz_status(self):
        """Reset quiz status if needed (e.g., retake)"""
        self.quiz_passed = False
        self.last_quiz_attempt_id = None
        self.is_completed = False
        self.completed_at = None
        self.save()
    
    def get_total_videos_count(self):
        """Helper to get total videos count"""
        return Video.objects.filter(
            curriculum_day__course=self.course
        ).count()
    
    def get_completed_videos_count(self):
        """Helper to get completed videos count"""
        return self.completed_videos.count()
    
    def get_completion_requirements(self):
        """Get completion requirements status"""
        total_videos = self.get_total_videos_count()
        completed_videos = self.get_completed_videos_count()
        quiz_passed = self.has_passed_quiz_actually()
        
        return {
            'total_videos': total_videos,
            'completed_videos': completed_videos,
            'videos_percentage': (completed_videos / total_videos * 100) if total_videos > 0 else 0,
            'quiz_passed': quiz_passed,
            'quiz_actually_passed': self.has_passed_quiz_actually(),
            'is_completed': self.is_completed,
            'requirements_met': {
                'videos': completed_videos == total_videos,
                'quiz': quiz_passed,
                'all': completed_videos == total_videos and quiz_passed
            }
        }
    
    def clean(self):
        """Validate model data"""
        from django.core.exceptions import ValidationError
        
        # If quiz_passed is True, verify we have a valid attempt ID
        if self.quiz_passed and not self.last_quiz_attempt_id:
            raise ValidationError({
                'quiz_passed': 'Cannot mark quiz as passed without a valid quiz attempt ID'
            })
        
        # If last_quiz_attempt_id is set, verify the attempt exists and is passed
        if self.last_quiz_attempt_id:
            try:
                from .models import QuizAttempt
                attempt = QuizAttempt.objects.get(id=self.last_quiz_attempt_id)
                
                # Verify it's for the same user and course
                if attempt.user != self.user:
                    raise ValidationError({
                        'last_quiz_attempt_id': 'Quiz attempt does not belong to this user'
                    })
                
                if attempt.quiz.course != self.course:
                    raise ValidationError({
                        'last_quiz_attempt_id': 'Quiz attempt is not for this course'
                    })
                
                # If quiz_passed is True but attempt is not passed, it's invalid
                if self.quiz_passed and not attempt.passed:
                    raise ValidationError({
                        'quiz_passed': 'Quiz attempt is not marked as passed'
                    })
                    
            except QuizAttempt.DoesNotExist:
                raise ValidationError({
                    'last_quiz_attempt_id': 'Quiz attempt does not exist'
                })
    
    def save(self, *args, **kwargs):
        """Override save to run validation and prevent invalid states"""
        # Run validation
        self.clean()
        
        # Prevent is_completed being True without actual completion
        if self.is_completed:
            requirements = self.get_completion_requirements()
            if not requirements['requirements_met']['all']:
                self.is_completed = False
                self.completed_at = None
        
        super().save(*args, **kwargs)


class Quiz(models.Model):
    """Quiz for a course"""
    course = models.OneToOneField('Course', on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    passing_score = models.IntegerField(default=70, help_text="Minimum percentage to pass")
    time_limit = models.IntegerField(default=30, help_text="Time limit in minutes (0 for no limit)")
    max_attempts = models.IntegerField(default=3, help_text="Maximum number of attempts (0 for unlimited)")
    show_correct_answers = models.BooleanField(default=True, help_text="Show correct answers after completion")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Quizzes'
    
    def __str__(self):
        return f"Quiz: {self.title} ({self.course.title})"
    
    def get_total_questions(self):
        return self.questions.count()


class Question(models.Model):
    QUESTION_TYPES = [
        ('single', 'Single Choice'),
        ('multiple', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='single')
    points = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    explanation = models.TextField(blank=True, help_text="Explanation shown after answering")
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class Answer(models.Model):
    """Answer options for questions"""
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['order', 'id']
    
    def __str__(self):
        return f"{self.answer_text} ({'Correct' if self.is_correct else 'Incorrect'})"


class QuizAttempt(models.Model):
    """Track quiz attempts by users"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    passed = models.BooleanField(default=False)
    time_taken = models.IntegerField(null=True, blank=True, help_text="Time taken in seconds")
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.quiz.title} - Score: {self.score}%"

    
    def calculate_score(self):
        """Calculate the score for this attempt"""
        # Ensure the attempt is actually completed
        if not self.completed_at:
            raise ValueError("Cannot calculate score for incomplete attempt")
        
        total_points = sum(q.points for q in self.quiz.questions.all())
        if total_points == 0:
            self.score = 0
            self.passed = False
            self.save()
            return 0
        
        earned_points = 0
        total_responses = self.responses.count()
        total_questions = self.quiz.questions.count()
        
        # Calculate earned points
        for response in self.responses.all():
            if response.is_correct():
                earned_points += response.question.points
        
        # Calculate percentage score
        score = (earned_points / total_points) * 100
        self.score = round(score, 2)
        self.passed = score >= self.quiz.passing_score
        self.save()
        
        # Update course progress if quiz is passed
        if self.passed:
            from .models import CourseProgress
            progress, created = CourseProgress.objects.get_or_create(
                user=self.user,
                course=self.quiz.course
            )
            
            # Use the new method to mark quiz as passed
            progress.mark_quiz_passed(self)
        
        return self.score


class QuizResponse(models.Model):
    """User's response to a quiz question"""
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answers = models.ManyToManyField(Answer)
    
    def __str__(self):
        return f"{self.attempt.user.email} - {self.question.question_text[:30]}"
    
    def is_correct(self):
        """Check if the response is correct"""
        correct_answers = set(self.question.answers.filter(is_correct=True))
        selected_answers = set(self.selected_answers.all())
        
        if self.question.question_type == 'single' or self.question.question_type == 'true_false':
            return len(selected_answers) == 1 and selected_answers == correct_answers
        elif self.question.question_type == 'multiple':
            return selected_answers == correct_answers
        return False


class Certificate(models.Model):
    """Certificate awarded upon course completion"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    certificate_id = models.CharField(max_length=50, unique=True, editable=False)
    issue_date = models.DateTimeField(auto_now_add=True)
    quiz_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    generated_image = models.CharField(max_length=255, blank=True, null=True)
    
    class Meta:
        unique_together = ['user', 'course']
        ordering = ['-issue_date']
    
    def __str__(self):
        return f"Certificate - {self.user.email} - {self.course.title}"
    
    def save(self, *args, **kwargs):
        if not self.certificate_id:
            self.certificate_id = uuid.uuid4().hex[:12].upper()
        
        # Get quiz score if available
        if not self.quiz_score:
            try:
                quiz_attempt = QuizAttempt.objects.filter(
                    user=self.user,
                    quiz__course=self.course,
                    passed=True
                ).order_by('-score').first()
                if quiz_attempt:
                    self.quiz_score = quiz_attempt.score
            except:
                pass
        
        super().save(*args, **kwargs)
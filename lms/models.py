from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.conf import settings
from ckeditor.fields import RichTextField
from django.utils import timezone
import uuid


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



# ============================
# COURSE REVIEW
# ============================
class CourseReview(models.Model):
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars')
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=RATING_CHOICES, default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'course']

    def __str__(self):
        return f"{self.user.email} - {self.course.title} ({self.rating} stars)"


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

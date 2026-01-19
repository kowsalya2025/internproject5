from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.text import Truncator
from .models import (
    User,
    HeroSection,
    FeatureSection,
    FeatureItem,
    HomeAboutSection,
    Category,
    CourseCategory,
    Instructor,
    Course,
    CourseTool,
    CurriculumDay,
    Video,
    Lesson,
    CourseReview,
    CourseEnrollment,
    Payment,
    Purchase,
    UserVideoProgress,
)


# ============================
# CUSTOM USER ADMIN
# ============================
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'first_name', 'last_name')}),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'username',
                'password1',
                'password2',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')


# ============================
# HERO SECTION ADMIN
# ============================
@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ('title_primary', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title_primary', 'title_secondary')


# ============================
# FEATURE SECTION ADMIN
# ============================
class FeatureItemInline(admin.TabularInline):
    model = FeatureItem
    extra = 1


@admin.register(FeatureSection)
class FeatureSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active')
    list_editable = ('is_active',)
    inlines = [FeatureItemInline]


# ============================
# HOME ABOUT SECTION ADMIN
# ============================
@admin.register(HomeAboutSection)
class HomeAboutSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview_list', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'subtitle', 'team_description')
    
    fieldsets = (
        ('Main Content', {
            'fields': ('title', 'subtitle', 'description', 'image', 'image_preview')
        }),
        ('Team Section', {
            'fields': ('team_title', 'team_description')
        }),
        ('Button Settings', {
            'fields': ('button_text', 'button_link')
        }),
        ('Settings', {
            'fields': ('is_active', 'order')
        }),
    )
    
    readonly_fields = ('image_preview', 'created_at', 'updated_at')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" style="border-radius: 5px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Image Preview'
    
    def image_preview_list(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />', obj.image.url)
        return "No Image"
    image_preview_list.short_description = 'Image'


# ============================
# CATEGORY ADMIN
# ============================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    ordering = ('order',)


# ============================
# COURSE CATEGORY ADMIN
# ============================
@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'order', 'course_count']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Number of Courses'


# ============================
# INSTRUCTOR ADMIN
# ============================
@admin.register(Instructor)
class InstructorAdmin(admin.ModelAdmin):
    list_display = ['name', 'designation','bio']
    search_fields = ['name']


# ============================
# COURSE INLINES
# ============================
class VideoInline(admin.TabularInline):
    model = Video
    extra = 1
    fields = ['title', 'description', 'duration', 'video_url', 'order', 'is_free']


class CurriculumDayInline(admin.TabularInline):
    model = CurriculumDay
    extra = 1
    fields = ['day_number', 'title', 'is_free', 'order']
    show_change_link = True



class CourseToolInline(admin.TabularInline):
    model = CourseTool
    extra = 1
    fields = ['tool_name']


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ['module_title', 'title', 'duration', 'is_preview', 'order']
    ordering = ['order']


class CourseReviewInline(admin.TabularInline):
    model = CourseReview
    extra = 0
    readonly_fields = ['user', 'rating', 'comment', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


# ============================
# COURSE ADMIN
# ============================
from django.contrib import admin
from django.utils.html import format_html
from .models import Course


from django.contrib import admin
from django.utils.html import format_html
from .models import Course

from django.contrib import admin
from django.utils.html import format_html
from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    # =========================
    # LIST PAGE
    # =========================
    list_display = (
        'title',
        'category',
        'level',
        'display_skills_icons',  # NEW: Skills icons
        'display_tools_icons',   # NEW: Tools icons
        'original_price',
        'discounted_price',
        'is_free',
        'is_active',
        'is_featured',
        'created_at',
        'total_learners',   # New field
        'payment_type',
    )

    list_filter = (
        'is_active',
        'is_featured',
        'is_free',
        'level',
        'category',
        'created_at',
    )

    search_fields = (
        'title',
        'short_description',
        'tagline',
        'skills',
        'tools_learned',
    )

    list_editable = (
        'is_active',
        'is_featured',
        'discounted_price',
    )

    ordering = ('-created_at',)

    date_hierarchy = 'created_at'

    # =========================
    # SLUG AUTO GENERATION
    # =========================
    prepopulated_fields = {
        'slug': ('title',)
    }

    # =========================
    # FORM LAYOUT
    # =========================
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'slug',
                'tagline',
                'short_description',
                'description',
            )
        }),

        ('Category & Instructors', {
            'fields': (
                'category',
                'instructors',
            )
        }),

        ('Pricing', {
            'fields': (
                'original_price',
                'discounted_price',
                'is_free',
            )
        }),

        ('Course Details', {
            'fields': (
                'level',
                'duration_hours',
                'languages',
                'access_level',
            )
        }),

        ('Course Content', {
            'fields': (
                'learning_outcomes',
                'prerequisites',
                'skills',
                'skills_icons_preview',  # NEW: Skills icons preview
                'tools_learned',
                'tools_icons_preview',   # NEW: Tools icons preview
                'certification_details',
            )
        }),

        ('Statistics', {
            'fields': (
                'total_videos',
                'total_projects',
                'total_resources',
            )
        }),

        ('Media', {
            'fields': (
                'thumbnail',
                'preview_video_url',
            )
        }),

        ('Status', {
            'fields': (
                'is_active',
                'is_featured',
            )
        }),

        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            )
        }),
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'skills_icons_preview',  # NEW
        'tools_icons_preview',   # NEW
    )

    # =========================
    # MANY-TO-MANY UX
    # =========================
    filter_horizontal = ('instructors',)

    # =========================
    # ADMIN ACTIONS
    # =========================
    actions = [
        'mark_active',
        'mark_inactive',
        'mark_featured',
    ]

    @admin.action(description="Mark selected courses as Active")
    def mark_active(self, request, queryset):
        queryset.update(is_active=True)

    @admin.action(description="Mark selected courses as Inactive")
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)

    @admin.action(description="Mark selected courses as Featured")
    def mark_featured(self, request, queryset):
        queryset.update(is_featured=True)

    # =========================
    # VISUAL POLISH
    # =========================
    save_on_top = True

    # =========================
    # SIMPLE METHODS WITHOUT format_html ERRORS
    # =========================
    
    def display_skills_icons(self, obj):
        """Simple text display for skills"""
        skills = obj.get_skills_list()[:3]
        if not skills:
            return '-'
        return ', '.join(skills)
    display_skills_icons.short_description = 'Skills'

    def display_tools_icons(self, obj):
        """Simple text display for tools"""
        tools = obj.get_tools_list()[:3]
        if not tools:
            return '-'
        return ', '.join(tools)
    display_tools_icons.short_description = 'Tools'

    def skills_icons_preview(self, obj):
        """Simple text preview without HTML"""
        if not obj.pk:
            return 'Save the course first to see skills'
        
        skills = obj.get_skills_list()
        if not skills:
            return 'No skills entered. Add comma-separated skills like: Python, Django, HTML, CSS'
        
        # Return plain text instead of HTML
        return f"Skills ({len(skills)}): {', '.join(skills)}"
    skills_icons_preview.short_description = 'Skills Preview'

    def tools_icons_preview(self, obj):
        """Simple text preview without HTML"""
        if not obj.pk:
            return 'Save the course first to see tools'
        
        tools = obj.get_tools_list()
        if not tools:
            return 'No tools entered. Add comma-separated tools like: VSCode, GitHub, Docker, Figma'
        
        # Return plain text instead of HTML
        return f"Tools ({len(tools)}): {', '.join(tools)}"
    tools_icons_preview.short_description = 'Tools Preview'

    # =========================
    # ADD FONT AWESOME CSS (SINGLE COPY)
    # =========================
    class Media:
        css = {
            'all': ('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',)
        }


# ============================
# CURRICULUM DAY ADMIN
# ============================
@admin.register(CurriculumDay)
class CurriculumDayAdmin(admin.ModelAdmin):
    list_display = ['course', 'day_number', 'title', 'is_free', 'order', 'video_count']
    list_filter = ['course', 'is_free']
    search_fields = ['course__title', 'title']
    inlines = [VideoInline]
    ordering = ['course', 'order', 'day_number']
    
    def video_count(self, obj):
        return obj.videos.count()
    video_count.short_description = 'Videos'


# ============================
# VIDEO ADMIN
# ============================
@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'curriculum_day', 'duration', 'is_free', 'order']
    list_filter = ['curriculum_day__course', 'is_free']
    search_fields = ['title', 'description']
    ordering = ['curriculum_day', 'order']
    
    fieldsets = (
        ('Video Information', {
            'fields': ('curriculum_day', 'title', 'description')
        }),
        ('Video Source', {
            'fields': ('video_url', 'video_file', 'thumbnail')
        }),
        ('Settings', {
            'fields': ('duration', 'order', 'is_free')
        }),
    )



# ============================
# LESSON ADMIN (Legacy)
# ============================
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'module_title', 'duration', 'is_preview', 'order']
    list_editable = ['order', 'is_preview']
    list_filter = ['course', 'is_preview', 'module_title']
    search_fields = ['title', 'content', 'module_title']
    list_select_related = ['course']
    
    fieldsets = (
        ('Lesson Information', {
            'fields': (
                'course',
                'module_title',
                'title',
                'content',
            )
        }),
        
        ('Media & Duration', {
            'fields': (
                'video_url',
                'duration',
            )
        }),
        
        ('Settings', {
            'fields': (
                'is_preview',
                'order',
            )
        }),
    )


# ============================
# PURCHASE ADMIN (New System)
# ============================
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'amount_paid', 'payment_status', 'purchased_at']
    list_filter = ['payment_status', 'purchased_at', 'course']
    search_fields = ['user__username', 'user__email', 'full_name', 'email', 'transaction_id']
    readonly_fields = ['purchased_at']
    date_hierarchy = 'purchased_at'
    
    fieldsets = (
        ('Purchase Information', {
            'fields': ('user', 'course', 'amount_paid', 'payment_status')
        }),
        ('Transaction Details', {
            'fields': ('transaction_id', 'purchased_at')
        }),
        ('User Details', {
            'fields': ('full_name', 'email')
        }),
    )




# ============================
# COURSE REVIEW ADMIN
# ============================
@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'user', 'rating_stars', 'truncated_comment', 'created_at', 'is_approved']
    list_editable = ['is_approved']
    list_filter = ['rating', 'is_approved', 'created_at', 'course']
    search_fields = ['comment', 'user__email', 'user__username', 'course__title']
    readonly_fields = ['course', 'user', 'rating', 'comment', 'created_at']
    list_select_related = ['course', 'user']
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html('<span style="color: #ffc107; font-size: 14px;">{}</span>', stars)
    rating_stars.short_description = 'Rating'
    
    def truncated_comment(self, obj):
        return Truncator(obj.comment).chars(50)
    truncated_comment.short_description = 'Comment'
    
    def has_add_permission(self, request):
        return False


# ============================
# COURSE ENROLLMENT ADMIN
# ============================
@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrollment_type', 'is_paid', 'enrolled_at', 'expires_at', 'course_link']
    list_filter = ['enrollment_type', 'is_paid', 'enrolled_at']
    search_fields = ['user__email', 'user__username', 'course__title', 'transaction_id']
    readonly_fields = ['enrolled_at']
    list_select_related = ['user', 'course']
    
    fieldsets = (
        ('Enrollment Information', {
            'fields': ('user', 'course', 'enrollment_type', 'is_paid')
        }),
        ('Dates', {
            'fields': ('enrolled_at', 'expires_at')
        }),
        ('Transaction', {
            'fields': ('transaction_id',)
        }),
    )
    
    def course_link(self, obj):
        url = reverse('admin:lms_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Course (Admin)'
    
    def has_add_permission(self, request):
        return False


# ============================
# PAYMENT ADMIN (Razorpay)
# ============================
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'amount', 'status', 'payment_method', 'payment_date', 'created_at')
    list_filter = ('status', 'currency', 'payment_date', 'created_at')
    search_fields = (
        'user__email', 
        'user__username', 
        'course__title', 
        'razorpay_order_id', 
        'razorpay_payment_id',
        'billing_email'
    )
    readonly_fields = ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature', 'created_at', 'updated_at')
    list_select_related = ['user', 'course']
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'course', 'amount', 'currency', 'status', 'payment_method')
        }),
        ('Razorpay Details', {
            'fields': ('razorpay_order_id', 'razorpay_payment_id', 'razorpay_signature')
        }),
        ('Billing Information', {
            'fields': (
                'billing_first_name', 'billing_last_name', 'billing_email', 'billing_phone',
                'billing_address', 'billing_city', 'billing_state', 'billing_zip_code', 'billing_country'
            ),
            'classes': ('collapse',)
        }),
        ('Additional Info', {
            'fields': ('notes', 'payment_date')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def mark_as_success(self, request, queryset):
        updated = queryset.update(status='success')
        self.message_user(request, f'{updated} payments marked as successful.')
    mark_as_success.short_description = "Mark selected payments as successful"
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} payments marked as failed.')
    mark_as_failed.short_description = "Mark selected payments as failed"


# ============================
# USER VIDEO PROGRESS ADMIN (Legacy)
# ============================
from django.contrib import admin
from .models import UserVideoProgress

@admin.register(UserVideoProgress)
class UserVideoProgressAdmin(admin.ModelAdmin):
    list_display = ('user', 'video', 'progress_percentage', 'is_completed', 'watched_duration_display', 'last_watched')
    list_filter = ('is_completed', 'last_watched')
    search_fields = ('user__email', 'user__username', 'video__title')
    readonly_fields = ('last_watched',)
    list_select_related = ['user', 'video', 'video__curriculum_day']
    
    # Add this method for progress_percentage
    def progress_percentage(self, obj):
        """
        Calculate and display progress as percentage
        """
        # Check if video has duration field
        if obj.video and hasattr(obj.video, 'duration'):
            if obj.video.duration > 0:
                # Assuming watched_duration is in seconds
                percentage = (obj.watched_duration / obj.video.duration) * 100
                return f"{percentage:.1f}%"
        return "0%"
    
    progress_percentage.short_description = 'Progress %'
    
    def watched_duration_display(self, obj):
        minutes = obj.watched_duration // 60
        seconds = obj.watched_duration % 60
        return f"{minutes}m {seconds}s"
    watched_duration_display.short_description = 'Watched Duration'


# ============================
# ADMIN SITE CUSTOMIZATION
# ============================
admin.site.site_header = "E-Learning Platform Admin"
admin.site.site_title = "E-Learning Admin Portal"
admin.site.index_title = "Welcome to E-Learning Platform Administration"


# homepage
from django.contrib import admin
from .models import HomeBanner

@admin.register(HomeBanner)
class HomeBannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'highlight_text', 'subtitle', 'button_text', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['title', 'subtitle', 'highlight_text']


from django.contrib import admin
from .models import Testimonial

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('name', 'role', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'role')

    from django.contrib import admin
from .models import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('question',)

from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')
    list_filter = ('subject', 'created_at')
    search_fields = ('name', 'email')

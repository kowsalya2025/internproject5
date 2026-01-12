from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    HeroSection,
    Category,
    Course,
    Lesson,
    Enrollment
)

# ============================
# Custom User Admin
# ============================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ('email',)
    list_display = ('email', 'username', 'is_staff', 'is_superuser', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username', 'phone')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('username', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')

# ============================
# Hero Section Admin
# ============================

@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    list_display = ('title_primary', 'is_active', 'created_at')
    list_editable = ('is_active',)
    search_fields = ('title_primary', 'title_secondary')



from django.contrib import admin
from .models import FeatureSection, FeatureItem


class FeatureItemInline(admin.TabularInline):
    model = FeatureItem
    extra = 1


@admin.register(FeatureSection)
class FeatureSectionAdmin(admin.ModelAdmin):
    list_display = ('title',)
    inlines = [FeatureItemInline]


# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import HomeAboutSection

@admin.register(HomeAboutSection)
class HomeAboutSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview_list', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    list_editable = ('is_active', 'order')
    search_fields = ('title', 'subtitle', 'team_description')
    
    fieldsets = (
        ('Main Content', {
            'fields': ('title', 'subtitle', 'image', 'image_preview')
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
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return "No Image"
    image_preview_list.short_description = 'Image'


# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.text import Truncator
from .models import CourseCategory, Instructor, Course, Lesson, CourseReview, Enrollment


# Custom Admin Classes
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'order', 'course_count']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Number of Courses'

class InstructorAdmin(admin.ModelAdmin):
    list_display = ['name', 'title', 'email', 'is_active', 'order', 'course_count', 'photo_preview']
    list_editable = ['is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['name', 'title', 'bio']
    
    def course_count(self, obj):
        return obj.courses.count()
    course_count.short_description = 'Courses'
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />', obj.photo.url)
        return "No Photo"
    photo_preview.short_description = 'Photo'

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

class CourseAdmin(admin.ModelAdmin):
    list_display = [
        'title', 
        'category', 
        'price_display', 
        'is_active', 
        'is_featured', 
        'level', 
        'order',
        'thumbnail_preview',
        'created_at'
    ]
    list_editable = ['is_active', 'is_featured', 'order']
    list_filter = ['is_active', 'is_featured', 'category', 'level', 'created_at']
    search_fields = ['title', 'short_description', 'tagline', 'instructors']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [LessonInline, CourseReviewInline]
    
    # Custom fieldsets for organized layout
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title', 
                'slug', 
                'tagline',
                'short_description', 
                'full_description',
                'category',
                'thumbnail',
                'page_url'
            )
        }),
        
        ('Pricing', {
            'fields': (
                'price',
                'is_free',
                'discount_price',
            ),
            'classes': ('collapse',)
        }),
        
        ('Course Details', {
            'fields': (
                'duration',
                'level',
                'instructors',
                'instructor',
            )
        }),
        
        ('Media & Content', {
            'fields': (
                'preview_video_url',
                'total_videos',
                'total_projects',
                'total_resources',
                'learning_outcomes',
                'prerequisites',
            ),
            'classes': ('collapse',)
        }),
        
        ('Status & Ordering', {
            'fields': (
                'is_featured',
                'is_active',
                'order',
            )
        }),
    )
    
    # Custom methods for list display
    def price_display(self, obj):
        if obj.is_free:
            return format_html('<span style="color: green; font-weight: bold;">FREE</span>')
        elif obj.is_on_discount:
            return format_html(
                '<span style="color: #ff4757; text-decoration: line-through;">${}</span> '
                '<span style="color: #50c878; font-weight: bold;">${}</span>',
                obj.price, obj.discount_price
            )
        else:
            return format_html('<span style="color: #2d3436;">${}</span>', obj.price)
    price_display.short_description = 'Price'
    
    def thumbnail_preview(self, obj):
        if obj.thumbnail:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.thumbnail.url)
        return "No Thumbnail"
    thumbnail_preview.short_description = 'Thumbnail'
    
    # Custom actions
    actions = ['make_featured', 'make_unfeatured', 'activate_courses', 'deactivate_courses']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} courses marked as featured.')
    make_featured.short_description = "Mark selected courses as featured"
    
    def make_unfeatured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} courses unmarked as featured.')
    make_unfeatured.short_description = "Mark selected courses as not featured"
    
    def activate_courses(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} courses activated.')
    activate_courses.short_description = "Activate selected courses"
    
    def deactivate_courses(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} courses deactivated.')
    deactivate_courses.short_description = "Deactivate selected courses"
    
    # Save method to ensure consistency
    def save_model(self, request, obj, form, change):
        if obj.is_free:
            obj.price = 0.00
            obj.discount_price = None
        super().save_model(request, obj, form, change)

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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('course')

class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ['course', 'user', 'rating_stars', 'truncated_comment', 'created_at', 'is_approved']
    list_editable = ['is_approved']
    list_filter = ['rating', 'is_approved', 'created_at', 'course']
    search_fields = ['comment', 'user__username', 'course__title']
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
        # Prevent adding reviews from admin (they should come from users)
        return False

class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'progress_display', 'completed', 'course_link']
    list_filter = ['completed', 'enrolled_at', 'course']
    search_fields = ['user__username', 'user__email', 'course__title']
    readonly_fields = ['user', 'course', 'enrolled_at']
    list_select_related = ['user', 'course']
    
    def progress_display(self, obj):
        color = '#50c878' if obj.progress == 100 else '#2d3436'
        return format_html(
            '<div style="background: #f1f2f6; border-radius: 10px; height: 10px; width: 100px; position: relative; display: inline-block; margin-right: 10px;">'
            '<div style="background: {}; width: {}%; height: 100%; border-radius: 10px;"></div>'
            '</div>'
            '<span>{}%</span>',
            color, obj.progress, obj.progress
        )
    progress_display.short_description = 'Progress'
    
    def course_link(self, obj):
        url = reverse('admin:courses_course_change', args=[obj.course.id])
        return format_html('<a href="{}">{}</a>', url, obj.course.title)
    course_link.short_description = 'Course (Admin)'
    
    def has_add_permission(self, request):
        # Prevent adding enrollments from admin (they should come from checkout)
        return False

# Register all models
admin.site.register(CourseCategory, CourseCategoryAdmin)
admin.site.register(Instructor, InstructorAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Lesson, LessonAdmin)
admin.site.register(CourseReview, CourseReviewAdmin)
admin.site.register(Enrollment, EnrollmentAdmin)

# Optional: Customize admin site header and title
admin.site.site_header = "E-Learning Platform Admin"
admin.site.site_title = "E-Learning Admin Portal"
admin.site.index_title = "Welcome to E-Learning Platform Administration"

class CourseReviewAdmin(admin.ModelAdmin):
    # In your methods that reference User, it will work correctly
    def truncated_comment(self, obj):
        return Truncator(obj.comment).chars(50)
    truncated_comment.short_description = 'Comment'
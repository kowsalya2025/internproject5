# lms/templatetags/course_filters.py
from django import template

register = template.Library()

@register.filter
def get_display_price(course):
    """Get display price for course"""
    if course.is_free:
        return "Free"
    if course.is_on_discount and course.discount_price:
        return f"${course.discount_price}"
    return f"${course.price}"

@register.filter
def get_original_price(course):
    """Get original price for display"""
    if course.is_free:
        return None
    if course.is_on_discount:
        return f"${course.price}"
    return None

@register.filter
def get_price_amount(course):
    """Get price amount (numeric)"""
    if course.is_on_discount:
        return course.discount_price
    return course.price

@register.filter
def get_discount_amount(course):
    """Get discount amount"""
    if course.is_on_discount:
        return course.discount_amount
    return 0

@register.filter(name='is_discounted')
def is_discounted(course):
    """Check if course is on discount"""
    return course.is_on_discount

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(key, 0)
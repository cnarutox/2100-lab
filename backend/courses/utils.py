from django.utils import timezone
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse

from customers.models import LearningLog, OrderLog
from courses.models import Course


def get_courses(course_type, limit=None):
    if course_type == 'free':
        courses = Course.objects.filter(price='0.00').order_by('-updated_at')
    elif course_type == 'paid':
        courses = Course.objects.exclude(price='0.00').order_by('-updated_at')
    else:
        courses = Course.objects.all().order_by('-updated_at')
    if limit:
        courses = courses[:limit]
    return courses


def can_access(course, customer):
    if course.is_free():
        return True
    try:
        OrderLog.objects.get(course=course, customer=customer, refunded_at=None)
        return True
    except OrderLog.DoesNotExist:
        return False


def check_learning_log(course, customer):
    try:
        learning_log = LearningLog.objects.get(course=course, customer=customer)
        learning_log.latest_learn = timezone.now()
        learning_log.save()
    except LearningLog.DoesNotExist:
        learning_log = LearningLog.objects.create(
            course=course,
            customer=customer,
            expire_time=course.expire_duration + timezone.now()
        )
    return learning_log.progress


def get_comment_page(request, items):
    count = items.count()
    page = request.GET.get('page')
    paginator = Paginator(items, request.GET.get('page_limit', 10))
    try:
        item_page = paginator.page(page)
    except (PageNotAnInteger, EmptyPage):
        item_page = paginator.page(1)
    item_list = list(
        map(lambda item: item.as_dict(customer=request.user), list(item_page))
    )
    return JsonResponse(
        {
            'count': count,
            'page': item_page.number,
            'num_pages': paginator.num_pages,
            'content': item_list
        },
        safe=False
    )

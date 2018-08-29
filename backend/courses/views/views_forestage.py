"""课程模块前台操作"""

import uuid

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from core.constants import ERROR, INFO
from core.utils import get_page
from courses import utils
from courses.models import Hero, Course, Image, Comment, CourseUpVotes
from customers.models import LearningLog, OrderLog


def get_heroes(request):
    """获取头图"""

    heroes = Hero.objects.all()
    count = heroes.count()
    json_data = {
        'count': count,
        'content': []
    }
    for hero in heroes:
        json_data['content'].append(hero.as_dict())
    return JsonResponse(json_data)


def get_recent_courses(request):
    """获取最近课程"""

    free_courses = utils.get_courses('free', 8)
    paid_courses = utils.get_courses('paid', 8)
    json_data = {
        'free_courses': [],
        'paid_courses': []
    }
    for free_course in free_courses:
        json_data['free_courses'].append(free_course.as_dict())
    for paid_course in paid_courses:
        json_data['paid_courses'].append(paid_course.as_dict())
    return JsonResponse(json_data)


def get_course_list(request):
    """获取课程列表"""

    courses = utils.get_courses(
        request.GET.get('course_type')
    ).order_by('-updated_at')
    return get_page(request, courses)


def get_course_detail(request):
    """获取课程详情"""

    course_id = request.GET.get('course_id')
    request.session['referer_id'] = request.GET.get('referer_id', '')

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    course_detail = {
        'course_id': course.id,
        'thumbnail': str(course.thumbnail),
        'title': course.title,
        'description': course.description,
        'price': course.price,
        'reward_percent': course.reward_percent,
        'up_votes': course.up_votes.count(),
        'up_voted': request.user in course.up_votes.all(),
        'expire_duration': course.expire_duration.total_seconds(),
        'expire_time': None,
        'can_access': False
    }
    if request.user.is_authenticated:
        try:
            learning_log = LearningLog.objects.get(
                course=course,
                customer=request.user
            )
            expire_time = learning_log.expire_time
            if expire_time is not None:
                course_detail['expire_time'] = expire_time
        except LearningLog.DoesNotExist:
            pass
        course_detail['can_access'] = utils.can_access(course, request.user)
    return JsonResponse(course_detail)


@login_required
def up_vote_course(request):
    """点赞课程"""

    course_id = request.GET.get('course_id')
    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    customer = request.user
    if customer in course.up_votes.all():
        up_voted = False
        CourseUpVotes.objects.get(course=course, customer=customer).delete()
    else:
        up_voted = True
        CourseUpVotes.objects.create(
            course=course,
            customer=customer
        )
    return JsonResponse(
        {
            'up_voted': up_voted,
            'up_votes': course.up_votes.count()
        }
    )


@login_required
def buy_course(request):
    """购买课程并完成分销"""

    course_id = request.POST.get('course_id')
    payment_method = request.POST.get('payment_method')
    customer = request.user

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    try:
        OrderLog.objects.get(customer=customer, course=course, refunded_at=None)
        return JsonResponse(
            {'message': ERROR['course_already_purchased']},
            status=400
        )
    except OrderLog.DoesNotExist:
        pass

    price = course.price
    reward_coin = customer.reward_coin
    referer_id = request.session['referer_id']
    reward_percent = course.reward_percent

    if price > reward_coin:
        cash_spent = price - reward_coin
        reward_spent = reward_coin
        reward_coin = 0
    else:
        cash_spent = 0
        reward_spent = price
        reward_coin -= price

    customer.reward_coin = reward_coin
    customer.save()

    if referer_id != '' and int(referer_id) != int(customer.id):
        referer_id = int(referer_id)
        try:
            referer = get_user_model().objects.get(id=referer_id)
            reward_get = reward_percent * price
            referer.reward_coin += reward_get
            referer.save()
        except Course.DoesNotExist:
            pass

    OrderLog.objects.create(
        order_no=uuid.uuid1(),
        customer=customer,
        course=course,
        cash_spent=cash_spent,
        reward_spent=reward_spent,
        payment_method=int(payment_method)
    )

    return JsonResponse({'message': INFO['success']})


@login_required
def get_course_assets(request):
    """获取课程资源"""

    course_id = request.GET.get('course_id')

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(course, request.user):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    progress = utils.check_learning_log(course, request.user)
    images = Image.objects.filter(course=course).all().order_by('load_time')
    json_data = {
        'course_id': course.id,
        'title': course.title,
        'description': course.description,
        'audio': str(course.audio),
        'images': [],
        'progress': progress
    }
    for image in images:
        json_data['images'].append(image.as_dict())

    return JsonResponse(json_data)


@login_required
def save_learning_log(request):
    """保存学习进度"""

    try:
        course = Course.objects.get(id=request.GET.get('course_id'))
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(course, request.user):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    try:
        learning_log = LearningLog.objects.get(
            course=course,
            customer=request.user
        )
    except LearningLog.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    learning_log.progress = request.GET.get('progress')
    learning_log.save()

    return JsonResponse({'message': INFO['success']})


@login_required
def get_course_comments(request):
    """获取课程下的评论"""

    try:
        course = Course.objects.get(id=request.GET.get('course_id'))
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(course, request.user):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    if not course.can_comment:
        return JsonResponse(
            {'message': ERROR['comment_not_allowed']},
            status=403
        )

    comments = Comment.objects.filter(
        course=course,
        parent__isnull=True
    ).order_by('-created_at')
    return utils.get_comment_page(request, comments)


@login_required
def delete_comment(request):
    """删除评论"""

    try:
        comment = Comment.objects.get(id=request.POST.get('comment_id'))
    except Comment.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not request.user.id == comment.user.id:
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    comment.delete()
    return JsonResponse({'message': INFO['object_deleted']})


@login_required
def up_vote_comment(request):
    """点赞评论"""

    customer = request.user

    try:
        comment = Comment.objects.get(id=request.GET.get('comment_id'))
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(comment.course, customer):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    if customer in comment.up_votes.all():
        up_voted = False
        comment.up_votes.remove(customer)
    else:
        up_voted = True
        comment.up_votes.add(customer)
    return JsonResponse(
        {
            'up_voted': up_voted,
            'up_votes': comment.up_votes.count()
        }
    )


@login_required
def down_vote_comment(request):
    """点踩课程"""

    customer = request.user

    try:
        comment = Comment.objects.get(id=request.GET.get('comment_id'))
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(comment.course, customer):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    if customer in comment.down_votes.all():
        down_voted = False
        comment.down_votes.remove(customer)
    else:
        down_voted = True
        comment.down_votes.add(customer)
    return JsonResponse(
        {
            'down_voted': down_voted,
            'down_votes': comment.down_votes.count()
        }
    )


@login_required
def add_comment(request):
    """添加评论"""

    user = request.user
    course_id = request.POST.get('course_id')
    reply_to_id = request.POST.get('reply_to_id', '')
    comment_content = request.POST.get('content')

    try:
        course = Course.objects.get(id=course_id)
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(course, request.user):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    if (not course.can_comment) or user.is_banned:
        return JsonResponse(
            {'message': ERROR['comment_not_allowed']},
            status=403
        )

    comment = Comment.objects.create(
        user=user,
        course=course,
        content=comment_content
    )

    if reply_to_id != '':
        try:
            reply_to = Comment.objects.get(id=int(reply_to_id))
            comment.parent = reply_to
            comment.save()
        except Comment.DoesNotExist:
            pass

    return JsonResponse(
        {
            'message': INFO['success'],
            'comment_id': comment.id
        }
    )


@login_required
def get_replies(request):
    """获取回复"""

    comment_id = request.GET.get('comment_id')

    try:
        comment = Comment.objects.get(id=comment_id)
    except Course.DoesNotExist:
        return JsonResponse({'message': ERROR['object_not_found']}, status=404)

    if not utils.can_access(comment.course, request.user):
        return JsonResponse({'message': ERROR['access_denied']}, status=403)

    if not comment.course.can_comment:
        return JsonResponse(
            {'message': ERROR['comment_not_allowed']},
            status=403
        )

    replies = Comment.objects.filter(parent=comment).order_by('-created_at')
    return utils.get_reply_page(request, replies)

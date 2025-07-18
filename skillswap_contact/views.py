import logging
from functools import wraps
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from typing import TYPE_CHECKING
from skillswap_common.models import UserProfile, Message, Messages

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from django.http import HttpRequest
    from django.db.models import QuerySet

TEMPLATE_CHAT_PAGE = 'skillswap/chat.html'
TEMPLATE_MESSAGES_PAGE = 'skillswap/messages.html'

def _send_message(user: 'User', to_uid: int, message: str):
    messages = Messages.get_messages_for(user)
    messages.send_message(to_uid, text=message)


def _request_user_is_same(request: 'HttpRequest', uid: int):
    return request.user.id == uid

@login_required
def contact_user(request: 'HttpRequest', uid: int) -> HttpResponse:
    if _request_user_is_same(request, uid):
        return HttpResponseBadRequest('Cannot chat with self')
    try:
        user = request.user
        if request.method == 'POST':
            message = request.POST['message']
            _send_message(user, to_uid=uid, message=message)
    except (KeyError, ValueError, UserProfile.DoesNotExist):
        # TODO Check text length, and that both users exist
        logger.exception('Error sending message')
        return JsonResponse({'success': False})
    return JsonResponse({'success': True})


@login_required
def api_messages(request: 'HttpRequest') -> HttpResponse:
    user = request.user
    messages = Messages.get_messages_for(user)
    return JsonResponse({'messages': [m.as_dict() for m in messages.messages.order_by('sent_at')]})


@login_required
def messages(request: 'HttpRequest') -> HttpResponse:
    user = request.user
    messages = Messages.get_messages_for(user)
    chats = {}
    for message in messages.messages.order_by('-sent_at'):
        to_other: 'Messages' = message.receiver if message.receiver.id != messages.id else message.sender
        if to_other.user.id not in chats:
            chats[to_other.user.id] = {
                'chat_with': to_other.user.username,
                'user': request.user,
                'last_message': message.for_template()
            }
    return render(request, TEMPLATE_MESSAGES_PAGE, context={'chats': chats, 'chat_base_url': 'skillswap_contact.chat'})


@login_required
def chat_with_user(request: 'HttpRequest', uid: int) -> HttpResponse:
    if _request_user_is_same(request, uid):
        return HttpResponseBadRequest('Cannot chat with self')
    all_messages = Messages.get_messages_for(request.user)
    to_other = Messages.get_messages_for(uid)
    messages_with_user = all_messages.get_chat_log_with(uid)
    if request.method == 'POST':
        try:
            contact_user(request, uid)
        except (KeyError, ValueError, UserProfile.DoesNotExist):
            raise
    context = {
        'chat': [m.for_template() for m in messages_with_user],
        'other': to_other.user,
        'user': request.user,
    }
    return render(request, TEMPLATE_CHAT_PAGE, context=context)

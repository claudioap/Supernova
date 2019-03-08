import random
import psutil
from django.core.cache import cache
from django.shortcuts import render

from users.forms import LoginForm
from kleep.models import Changelog, Catchphrase
from settings import VERSION
from news.models import NewsItem


def index(request):
    context = build_base_context(request)
    context['title'] = "O sistema que não deixa folhas soltas"
    context['news'] = NewsItem.objects.order_by('datetime').reverse()[0:5]
    context['changelog'] = Changelog.objects.order_by('date').reverse()[0:3]
    context['catchphrase'] = random.choice(Catchphrase.objects.all())
    return render(request, 'kleep/index.html', context)


def about(request):
    context = build_base_context(request)
    context['title'] = "Sobre"
    context['version'] = VERSION
    return render(request, 'kleep/about.html', context)


def beg(request):
    context = build_base_context(request)
    context['title'] = "Ajudas"
    return render(request, 'kleep/beg.html', context)


def privacy(request):
    context = build_base_context(request)
    context['title'] = "Política de privacidade"
    return render(request, 'kleep/privacy.html', context)


def build_base_context(request):
    result = {'disable_auth': False,
              'sub_nav': None,
              'cpu': __cpu_load(),
              'people': 0  # TODO
              }
    if not request.user.is_authenticated:
        result['login_form'] = LoginForm()
    return result


def __cpu_load():
    cpu_load_val = cache.get('cpu_load')
    if cpu_load_val is None:
        cpu_load_val = psutil.cpu_percent(interval=0.10)  # cache instead of calculating for every request
        cache.set('cpu_load', cpu_load_val, 10)

    if cpu_load_val <= 50.0:
        return 0  # low
    elif cpu_load_val <= 80.0:
        return 1  # medium
    else:
        return 2  # high

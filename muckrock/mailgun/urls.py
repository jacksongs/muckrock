"""
URL mappings for mailgun
"""

from django.conf.urls import patterns, url

from muckrock.mailgun import views

urlpatterns = patterns(
    '',
    url(
        r'^route/$',
        views.route_mailgun,
        name='mailgun-route'
    ),
    url(
        r'^bounces/$',
        views.bounces,
        name='mailgun-bounces'
    ),
    url(
        r'^opened/$',
        views.opened,
        name='mailgun-opened'
    ),
    url(
        r'^delivered/$',
        views.delivered,
        name='mailgun-delivered'
    ),
    url(
        r'^phaxio/$',
        views.phaxio_callback,
        name='phaxio-callback'
    ),
)

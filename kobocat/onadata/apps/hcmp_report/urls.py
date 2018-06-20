from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.planmodule import views, views_api

urlpatterns = patterns('',
                       url(r'^$', views.index, name='index'),


                       )

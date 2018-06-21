from django.conf.urls import patterns, include, url
from django.contrib import admin
from onadata.apps.hcmp_report import views

urlpatterns = patterns('',
    url(r'^tb_hiv/$', views.tb_hiv, name='tb_hiv'),
    url(r'^get_geodata/(?P<tag>[^/]+)/$', views.get_geodata, name='get_geodata'),
    url(r'^get_tb_hiv_data_table/$', views.get_tb_hiv_data_table, name='get_tb_hiv_data_table'),
    url(r'^malaria/$', views.malaria, name='tb_hiv'),
    url(r'^get_malaria_data_table/$', views.get_malaria_data_table, name='get_malaria_data_table'),
    url(r'^immunization/$', views.immunization, name='immunization'),
    url(r'^get_immunization_data_table/$', views.get_immunization_data_table, name='get_immunization_data_table'),


                       )

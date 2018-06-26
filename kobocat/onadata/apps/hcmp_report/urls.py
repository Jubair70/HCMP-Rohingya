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
    url(r'^outbreak_disease/$', views.outbreak_disease, name='outbreak_disease'),
    url(r'^get_outbreak_disease_data_table/$', views.get_outbreak_disease_data_table, name='get_outbreak_disease_data_table'),
    url(r'^health/$', views.health, name='health'),
    url(r'^get_health_data_table/$', views.get_health_data_table, name='get_health_data_table'),
    url(r'^wfp_nutrition/$', views.wfp_nutrition, name='wfp_nutrition'),
    url(r'^get_wfp_nutrition_data_table/$', views.get_wfp_nutrition_data_table, name='get_wfp_nutrition_data_table'),
    url(r'^unicef_nutrition/$', views.unicef_nutrition, name='unicef_nutrition'),
    url(r'^get_unicef_nutrition_data_table/$', views.get_unicef_nutrition_data_table, name='get_unicef_nutrition_data_table'),
    url(r'^education_student/$', views.education_student, name='education_student'),
    url(r'^get_education_student_data_table/$', views.get_education_student_data_table, name='get_education_student_data_table'),
    url(r'^education_teacher/$', views.education_teacher, name='education_teacher'),
    url(r'^get_education_teacher_data_table/$', views.get_education_teacher_data_table, name='get_education_teacher_data_table'),
    url(r'^wash/$', views.wash, name='wash'),
    url(r'^get_wash_data_table/$', views.get_wash_data_table, name='get_wash_data_table'),
    url(r'^agriculture_fdmn/$', views.agriculture_fdmn, name='agriculture_fdmn'),
    url(r'^get_agriculture_fdmn_data_table/$', views.get_agriculture_fdmn_data_table, name='get_agriculture_fdmn_data_table'),
    url(r'^agriculture_host/$', views.agriculture_host, name='agriculture_host'),
    url(r'^get_agriculture_host_data_table/$', views.get_agriculture_host_data_table, name='get_agriculture_host_data_table'),
    url(r'^cfs_fdmn/$', views.cfs_fdmn, name='cfs_fdmn'),
    url(r'^get_cfs_fdmn_data_table/$', views.get_cfs_fdmn_data_table, name='get_cfs_fdmn_data_table'),
    url(r'^cfs_host/$', views.cfs_host, name='cfs_host'),
    url(r'^get_cfs_host_data_table/$', views.get_cfs_host_data_table, name='get_cfs_host_data_table'),
    url(r'^cfs_summary/$', views.cfs_summary, name='cfs_summary/'),
    url(r'^get_cfs_summary_data_table/$', views.get_cfs_summary_data_table, name='get_cfs_summary_data_table'),
    url(r'^pss/$', views.pss, name='pss'),
    url(r'^get_pss_data_table/$', views.get_pss_data_table, name='get_pss_data_table'),
    url(r'^c4d/$', views.c4d, name='c4d'),
    url(r'^get_c4d_data_table/$', views.get_c4d_data_table, name='get_c4d_data_table'),
    url(r'^gbv/$', views.gbv, name='gbv'),
    url(r'^get_gbv_data_table/$', views.get_gbv_data_table, name='get_gbv_data_table'),
url(r'^nfi_fdmn/$', views.nfi_fdmn, name='nfi_fdmn'),
    url(r'^get_nfi_fdmn_data_table/$', views.get_nfi_fdmn_data_table, name='get_nfi_fdmn_data_table'),
url(r'^nfi_host/$', views.nfi_host, name='nfi_host'),
    url(r'^get_nfi_host_data_table/$', views.get_nfi_host_data_table, name='get_nfi_host_data_table'),
url(r'^drr_nfi/$', views.drr_nfi, name='drr_nfi'),
    url(r'^get_drr_nfi_data_table/$', views.get_drr_nfi_data_table, name='get_drr_nfi_data_table'),






                       )

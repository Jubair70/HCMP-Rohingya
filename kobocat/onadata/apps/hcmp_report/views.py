#!/usr/bin/env python
# -*- coding: utf-8 -*-
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.db.models import Count, Q
from django.http import (
    HttpResponseRedirect, HttpResponse)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.models import User
from datetime import date, timedelta, datetime
# from django.utils import simplejson
import json
import logging
import sys
import operator
import pandas
from django.shortcuts import render
import numpy
import time
import datetime
from django.core.files.storage import FileSystemStorage

from django.core.urlresolvers import reverse

from django.db import (IntegrityError, transaction)
from django.db.models import ProtectedError
from django.shortcuts import redirect
from onadata.apps.main.models.user_profile import UserProfile
from onadata.apps.usermodule.forms import UserForm, UserProfileForm, ChangePasswordForm, UserEditForm, OrganizationForm, \
    OrganizationDataAccessForm, ResetPasswordForm
from onadata.apps.usermodule.models import UserModuleProfile, UserPasswordHistory, UserFailedLogin, Organizations, \
    OrganizationDataAccess

from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
# Menu imports
from onadata.apps.usermodule.forms import MenuForm
from onadata.apps.usermodule.models import MenuItem
# Unicef Imports
from onadata.apps.logger.models import Instance, XForm
# Organization Roles Import
from onadata.apps.usermodule.models import OrganizationRole, MenuRoleMap, UserRoleMap
from onadata.apps.usermodule.forms import OrganizationRoleForm, RoleMenuMapForm, UserRoleMapForm, UserRoleMapfForm
from django.forms.models import inlineformset_factory, modelformset_factory
from django.forms.formsets import formset_factory

from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from collections import OrderedDict
import decimal
import csv
import os
import zipfile
from io import BytesIO

SECTOR_LIST = [{'name': 'Health', 'value': 1}, {'name': 'Nutrition', 'value': 2}, {'name': 'Education', 'value': 3},
               {'name': 'Wash', 'value': 4}, {'name': 'Agriculture & Environment', 'value': 5},
               {'name': 'Child Protection', 'value': 6}, {'name': 'C4D', 'value': 7},
               {'name': 'GBV', 'value': 8}, {'name': 'Shelter/NFI', 'value': 9},
               {'name': 'DRR', 'value': 10}, {'name': 'Training', 'value': 11},
               {'name': 'Site Management', 'value': 12}, {'name': 'Communication', 'value': 13}]


def __db_fetch_values(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchall()
    cursor.close()
    return fetchVal


def __db_fetch_single_value(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = cursor.fetchone()
    cursor.close()
    return fetchVal[0]


def __db_fetch_values_dict(query):
    cursor = connection.cursor()
    cursor.execute(query)
    fetchVal = dictfetchall(cursor)
    cursor.close()
    return fetchVal


def __db_commit_query(query):
    cursor = connection.cursor()
    cursor.execute(query)
    connection.commit()
    cursor.close()


def dictfetchall(cursor):
    desc = cursor.description
    return [
        OrderedDict(zip([col[0] for col in desc], row))
        for row in cursor.fetchall()]


def makeTableList(tableListQuery):
    cursor = connection.cursor()
    cursor.execute(tableListQuery)
    tableList = list(cursor.fetchall())
    return tableList


def decimal_date_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        return obj
    raise TypeError


def get_geodata(request, tag):
    id = request.POST.get('id')
    if tag == 'branch':
        query_part = " where upazila_id = " + id
    elif tag == 'camp':
        query_part = " where branch_id = " + id
    elif tag == 'unions':
        query_part = " where upazila_id = " + id
    elif tag == 'village':
        query_part = " where union_id = " + id
    else:
        query_part = ""
    q = "select id,name from " + tag + "" + query_part
    list = makeTableList(q)
    jsonlist = json.dumps({'data_list': list}, default=decimal_date_default)

    return HttpResponse(jsonlist)


def get_dates(daterange):
    date_list = daterange.split('-')
    data = {
        'start_date': date_list[0], 'end_date': date_list[1]
    }
    return data


@login_required
def tb_hiv(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/tb_hiv.html', {'upz_list': upz_list})


def get_tb_hiv_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    if date_range == '':
        start_date = '06/01/2018'
        end_date = '06/28/2018'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')

    q = "select * from get_rpt_health_tb('" + start_date + "','" + end_date + "','','','')"
    dataset = __db_fetch_values_dict(q)
    datalist = []
    data_dict = {}
    for temp in dataset:
        data_dict['particulars'] = temp['_particulars']
        data_dict['male'] = temp['_male']
        data_dict['female'] = temp['_female']
        data_dict['less_5_male'] = temp['_less_5_male']
        data_dict['less_5_female'] = temp['_less_5_female']
        data_dict['greater_5_male'] = temp['_greater_5_male']
        data_dict['greater_5_female'] = temp['_greate_5_female']
        data_dict['total'] = temp['_total']
        datalist.append(data_dict.copy())
        data_dict.clear()

    return render(request, 'hcmp_report/tb_hiv_table.html', {'dataset': datalist})


@login_required
def malaria(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/malaria.html', {'upz_list': upz_list})


def get_malaria_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_maleria('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    datalist = []
    data_dict = {}
    for temp in dataset:
        data_dict['particulars'] = temp['_particulars']
        data_dict['male'] = temp['_male']
        data_dict['female'] = temp['_female']
        data_dict['less_5_male'] = temp['_less_5_male']
        data_dict['less_5_female'] = temp['_less_5_female']
        data_dict['greater_5_male'] = temp['_greater_5_male']
        data_dict['greater_5_female'] = temp['_greate_5_female']
        data_dict['total'] = temp['_total']
        datalist.append(data_dict.copy())
        data_dict.clear()

    return render(request, 'hcmp_report/malaria_table.html', {'dataset': datalist})


@login_required
def immunization(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/immunization.html', {'upz_list': upz_list})


def get_immunization_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_immunization('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    datalist = []
    data_dict = {}
    for temp in dataset:
        data_dict['particulars'] = temp['_particulars']
        data_dict['total'] = temp['_total']
        datalist.append(data_dict.copy())
        data_dict.clear()

    return render(request, 'hcmp_report/immunization_table.html', {'dataset': datalist})


@login_required
def outbreak_disease(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/outbreak_disease.html', {'upz_list': upz_list})


def get_outbreak_disease_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_outbreak_disease('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)

    return render(request, 'hcmp_report/outbreak_disease_table.html', {'dataset': dataset})


@login_required
def health(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/health.html', {'upz_list': upz_list})


def get_health_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    # 1st report
    q_1 = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset_1 = __db_fetch_values_dict(q_1)
    # 2nd report
    q_2 = "select * from get_rpt_health_2('06/01/2018','06/28/2018','','','')"
    dataset_2 = __db_fetch_values_dict(q_2)
    return render(request, 'hcmp_report/health_table.html', {'dataset': dataset_1, 'dataset_2': dataset_2})


@login_required
def wfp_nutrition(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/wfp_nutrition.html', {'upz_list': upz_list})


def get_wfp_nutrition_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/wfp_nutrition_table.html', {'dataset': dataset})


@login_required
def unicef_nutrition(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/unicef_nutrition.html', {'upz_list': upz_list})


def get_unicef_nutrition_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/unicef_nutrition_table.html', {'dataset': dataset})


@login_required
def education_student(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/education_student.html', {'upz_list': upz_list})


def get_education_student_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_education_student('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/education_student_table.html', {'dataset': dataset})


@login_required
def education_teacher(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/education_teacher.html', {'upz_list': upz_list})


def get_education_teacher_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_education_teacher('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/education_teacher_table.html', {'dataset': dataset})


@login_required
def wash(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/wash.html', {'upz_list': upz_list})


def get_wash_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/wash_table.html', {'dataset': dataset})


@login_required
def agriculture_fdmn(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/agriculture_fdmn.html', {'upz_list': upz_list})


def get_agriculture_fdmn_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_agriculture_fdmn('06/01/2018','06/28/2018','','','');"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/agriculture_fdmn_table.html', {'dataset': dataset})


@login_required
def agriculture_host(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/agriculture_host.html', {'upz_list': upz_list})


def get_agriculture_host_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_agriculture_community('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/agriculture_host_table.html', {'dataset': dataset})


@login_required
def cfs_fdmn(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/cfs_fdmn.html', {'upz_list': upz_list})


def get_cfs_fdmn_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/cfs_fdmn_table.html', {'dataset': dataset})


@login_required
def cfs_host(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/cfs_host.html', {'upz_list': upz_list})


def get_cfs_host_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/cfs_host_table.html', {'dataset': dataset})


@login_required
def cfs_summary(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/cfs_summary.html', {'upz_list': upz_list})


def get_cfs_summary_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/cfs_summary_table.html', {'dataset': dataset})


@login_required
def pss(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/pss.html', {'upz_list': upz_list})


def get_pss_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/pss_table.html', {'dataset': dataset})


@login_required
def c4d(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/c4d.html', {'upz_list': upz_list})


def get_c4d_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/c4d_table.html', {'dataset': dataset})


@login_required
def gbv(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/gbv.html', {'upz_list': upz_list})


def get_gbv_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/gbv_table.html', {'dataset': dataset})


@login_required
def nfi_fdmn(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/nfi_fdmn.html', {'upz_list': upz_list})


def get_nfi_fdmn_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/nfi_fdmn_table.html', {'dataset': dataset})


@login_required
def nfi_host(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/nfi_host.html', {'upz_list': upz_list})


def get_nfi_host_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/nfi_host_table.html', {'dataset': dataset})


@login_required
def drr_nfi(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/drr_nfi.html', {'upz_list': upz_list})


def get_drr_nfi_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/drr_nfi_table.html', {'dataset': dataset})


@login_required
def drr_wash(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/drr_wash.html', {'upz_list': upz_list})


def get_drr_wash_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/drr_wash_table.html', {'dataset': dataset})


@login_required
def training(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/training.html', {'SECTOR_LIST': SECTOR_LIST})


def get_training_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/training_table.html', {'dataset': dataset})


# ------------------- Shahin ------------------------------ #


@login_required
def branch_list(request):
    branch_list = __db_fetch_values_dict("select id,row_number() OVER () as serial_no,name,code from branch")
    return render(request, 'hcmp_report/branch_list.html', {'branch_list': json.dumps(branch_list)})


@login_required
def add_branch_form(request):
    upazila_list = __db_fetch_values_dict(
        "select id as upazila_id,field_name as upazila_name from geo_data where field_type_id = 88")
    if request.method == 'POST':
        branch_name = request.POST.get('branch_name')
        branch_code = request.POST.get('branch_code')
        upazila_id = request.POST.get('upazila_id')

        __db_commit_query(
            "INSERT INTO public.branch (name, code, upazila_id) VALUES('" + str(branch_name) + "', '" + str(
                branch_code) + "', " + str(upazila_id) + ");")
        return HttpResponseRedirect('/hcmp_report/branch_list/')

    return render(request, 'hcmp_report/add_edit_branch_form.html', {'upazila_list': upazila_list})


@login_required
def edit_branch_form(request, branch_id):
    upazila_list = __db_fetch_values_dict(
        "select id as upazila_id,field_name as upazila_name from geo_data where field_type_id = 88")
    branch_info = __db_fetch_values_dict("select * from branch where id = " + str(branch_id))
    if request.method == 'POST':
        branch_name = request.POST.get('branch_name')
        branch_code = request.POST.get('branch_code')
        upazila_id = request.POST.get('upazila_id')

        __db_commit_query(
            "update branch set name = '" + str(branch_name) + "',code= '" + str(branch_code) + "',upazila_id = " + str(
                upazila_id) + " where id = " + str(branch_id))
        return HttpResponseRedirect('/hcmp_report/branch_list/')

    return render(request, 'hcmp_report/edit_branch_form.html', {
        'upazila_list': upazila_list,
        'branch_info': branch_info
    })


@login_required
def delete_branch(request, branch_id):
    delete_query = "delete from branch where id = " + str(branch_id) + ""
    __db_commit_query(delete_query)
    return HttpResponseRedirect("/hcmp_report/branch_list/")




@login_required
def camp_list(request):
    camp_list = __db_fetch_values_dict("select id,row_number() OVER () as serial_no,name,code,(select name from branch where id = branch_id) as branch from camp")
    return render(request, 'hcmp_report/camp_list.html', {'camp_list': json.dumps(camp_list)})


@login_required
def add_camp_form(request):
    branch_list = __db_fetch_values_dict(
        "select id as branch_id,name as branch_name from branch")
    if request.method == 'POST':
        camp_name = request.POST.get('camp_name')
        camp_code = request.POST.get('camp_code')
        branch_id = request.POST.get('branch_id')

        __db_commit_query(
            "INSERT INTO public.camp (name, code, branch_id) VALUES('" + str(camp_name) + "', '" + str(
                camp_code) + "', " + str(branch_id) + ");")
        return HttpResponseRedirect('/hcmp_report/camp_list/')

    return render(request, 'hcmp_report/add_camp_form.html', {'branch_list': branch_list})


@login_required
def edit_camp_form(request, camp_id):
    branch_list = __db_fetch_values_dict(
        "select id as branch_id,name as branch_name from branch")
    camp_info = __db_fetch_values_dict("select * from camp where id = " + str(camp_id))
    if request.method == 'POST':
        camp_name = request.POST.get('camp_name')
        camp_code = request.POST.get('camp_code')
        branch_id = request.POST.get('branch_id')

        __db_commit_query(
            "update camp set name = '" + str(camp_name) + "',code= '" + str(camp_code) + "',branch_id = " + str(
                branch_id) + " where id = " + str(camp_id))
        return HttpResponseRedirect('/hcmp_report/camp_list/')

    return render(request, 'hcmp_report/edit_camp_form.html', {
        'branch_list': branch_list,
        'camp_info': camp_info
    })


@login_required
def delete_camp(request, camp_id):
    delete_query = "delete from camp where id = " + str(camp_id) + ""
    __db_commit_query(delete_query)
    return HttpResponseRedirect("/hcmp_report/camp_list/")



@csrf_exempt
def get_geolocation_csv(request,id_string):

    both = ['cfs','shelter_nfi','agri_evironement']
    notapp = ['visitor','training','meeting']
    filenames = []

    if id_string not in notapp:
        geolocation_data = __db_fetch_values("select (select field_name from geo_data where id = (select field_parent_id from geo_data where id = gd.field_parent_id)) as upazila,(select field_name from geo_data where id = gd.field_parent_id limit 1) as union_name,field_name as village from geo_data gd where field_type_id = 92")
        branch_camp_data = __db_fetch_values("select (select field_name from geo_data where id = upazila_id) as upazila,branch.name as branch,camp.name as camp from camp left join branch on branch.id = camp.branch_id")
        try:
            os.stat("onadata/media/geodata/"+str(id_string)+"/")
        except:
            os.mkdir("onadata/media/geodata/"+str(id_string)+"/")

        if id_string in both:
            writer = csv.writer(open("onadata/media/geodata/"+str(id_string)+"/village.csv", 'w'))
            writer.writerow(['upazila', 'union_name', 'village'])
            for data in geolocation_data:
                writer.writerow([data[0], data[1], data[2]])

            filenames.append(request.META['HTTP_HOST']+"/media/geodata/"+str(id_string)+"/village.csv")

        writer2 = csv.writer(open("onadata/media/geodata/"+str(id_string)+"/camp.csv", 'w'))
        writer2.writerow(['upazila', 'branch', 'camp'])

        for data in branch_camp_data:
            writer2.writerow([data[0], data[1], data[2]])

        filenames.append(request.META['HTTP_HOST']+"/media/geodata/"+str(id_string)+"/camp.csv")


        resp = {
            'module_name': id_string
        }

        for fpath in filenames:
            resp[fpath.split('/')[-1].split('.')[0]+'_csv'] = fpath

        print request.META['HTTP_HOST']


    return HttpResponse(json.dumps(resp))


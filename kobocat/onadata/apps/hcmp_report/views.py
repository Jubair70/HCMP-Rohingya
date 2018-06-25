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
import os




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



def get_geodata(request,tag):
    id = request.POST.get('id')
    if tag=='branch':
        query_part = " where upazila_id = "+id
    elif tag == 'camp':
        query_part = " where branch_id = " + id
    q = "select id,name from "+tag+""+query_part
    list = makeTableList(q)
    jsonlist = json.dumps({'data_list': list}, default=decimal_date_default)

    return HttpResponse(jsonlist)



@login_required
def tb_hiv(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/tb_hiv.html',{'upz_list':upz_list})


def get_tb_hiv_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_tb('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    datalist=[]
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

    return render(request, 'hcmp_report/tb_hiv_table.html',{'dataset':datalist})




@login_required
def malaria(request):
    q = "select id,name from upazila"
    upz_list = makeTableList(q)
    return render(request, 'hcmp_report/malaria.html',{'upz_list':upz_list})


def get_malaria_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = request.POST.get('upazila')
    branch = request.POST.get('branch')
    camp = request.POST.get('camp')
    q = "select * from get_rpt_health_maleria('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    datalist=[]
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

    return render(request, 'hcmp_report/malaria_table.html',{'dataset':datalist})


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
    datalist=[]
    data_dict = {}
    for temp in dataset:
        data_dict['particulars'] = temp['_particulars']
        data_dict['total'] = temp['_total']
        datalist.append(data_dict.copy())
        data_dict.clear()

    return render(request, 'hcmp_report/immunization_table.html',{'dataset':datalist})


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
    q = "select * from get_rpt_health_immunization('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    datalist=[]
    data_dict = {}
    for temp in dataset:
        data_dict['particulars'] = temp['_particulars']
        data_dict['total'] = temp['_total']
        datalist.append(data_dict.copy())
        data_dict.clear()

    return render(request, 'hcmp_report/outbreak_disease_table.html',{'dataset':datalist})


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
    #1st report
    q_1 = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset_1 = __db_fetch_values_dict(q_1)
    #2nd report
    q_2 = "select * from get_rpt_health_2('06/01/2018','06/28/2018','','','')"
    dataset_2 = __db_fetch_values_dict(q_2)
    return render(request, 'hcmp_report/health_table.html',{'dataset':dataset_1,'dataset_2' : dataset_2})


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
    return render(request, 'hcmp_report/wfp_nutrition_table.html',{'dataset':dataset})



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
    return render(request, 'hcmp_report/unicef_nutrition_table.html',{'dataset':dataset})


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
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/education_student_table.html',{'dataset':dataset})


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
    q = "select * from get_rpt_health_1('06/01/2018','06/28/2018','','','')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/education_teacher_table.html',{'dataset':dataset})


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
    return render(request, 'hcmp_report/wash_table.html',{'dataset':dataset})
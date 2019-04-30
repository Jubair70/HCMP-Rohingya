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
from django.conf import settings
import StringIO
from pandas import ExcelWriter
import pandas as pd
import datetime


from django.utils.encoding import smart_str, smart_unicode


SECTOR_LIST = [{'name': 'Health', 'value': 8}, {'name': 'Nutrition', 'value': 9}, {'name': 'Education', 'value': 6},
               {'name': 'Wash', 'value': 10}, {'name': 'Agriculture & Environment', 'value': 1},
               {'name': 'Child Protection', 'value': 3}, {'name': 'C4D', 'value': 2},
               {'name': 'GBV', 'value': 7}, {'name': 'Shelter/NFI', 'value': 10},
               {'name': 'DRR', 'value': 5}, {'name': 'Training', 'value': 12},
               {'name': 'Site Management', 'value': 11}, {'name': 'Communication', 'value': 4}]


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
        q = "select id,name from " + tag + "" + query_part
    elif tag == 'camp':
        query_part = " where branch_id = " + id
        q = "select id,name from " + tag + "" + query_part
    elif tag == 'unions':
        query_part = " where field_parent_id = " + id
        q = "select id,field_name as name from geo_data " + query_part
    elif tag == 'village':
        query_part = " where field_parent_id = " + id
        q = "select id,field_name as name from geo_data " + query_part
    else:
        q = ""
        query_part = ""

    list = makeTableList(q)
    jsonlist = json.dumps({'data_list': list}, default=decimal_date_default)

    return HttpResponse(jsonlist)

def get_sector_list():
    q = "select id,sector_name from sector "
    sector_list = makeTableList(q)
    return sector_list


def get_upz_list():
    q = "select id,field_name from geo_data where field_type_id = 88"
    upz_list = makeTableList(q)
    return upz_list



def get_code(id):
    if id != '%':
        code = __db_fetch_single_value("select geocode from geo_data where id  =  "+str(int(id))+" ")
    else:
        code = id
    return code

def get_branch_code(branch_id):
    if branch_id != '%':
        code = __db_fetch_single_value("select code from branch where id  =  "+str(int(branch_id))+" ")
    else:
        code = branch_id
    return code

def get_camp_code(camp_id):
    if camp_id != '%':
        code = __db_fetch_single_value("select code from camp where id  =  "+str(int(camp_id))+" ")
    else:
        code = camp_id
    return code



def get_dates(daterange):
    date_list = daterange.split('-')
    data = {
        'start_date': date_list[0], 'end_date': date_list[1]
    }
    return data


@login_required
def tb_hiv(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/tb_hiv.html', {'upz_list': upz_list})


def get_tb_hiv_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))

    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_health_tb('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
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
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/malaria.html', {'upz_list': upz_list})


def get_malaria_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_health_maleria('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
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
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/immunization.html', {'upz_list': upz_list})


def get_immunization_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_health_immunization('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
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
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/outbreak_disease.html', {'upz_list': upz_list})


def get_outbreak_disease_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_health_outbreak_disease('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
    dataset = __db_fetch_values_dict(q)

    return render(request, 'hcmp_report/outbreak_disease_table.html', {'dataset': dataset})


@login_required
def health(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/health.html', {'upz_list': upz_list})


def get_health_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    # 1st report
    q_1 = "select * from get_rpt_health_1('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
    dataset_1 = __db_fetch_values_dict(q_1)
    # 2nd report
    q_2 = "select * from get_rpt_health_2('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
    dataset_2 = __db_fetch_values_dict(q_2)
    return render(request, 'hcmp_report/health_table.html', {'dataset': dataset_1, 'dataset_2': dataset_2})


@login_required
def wfp_nutrition(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/wfp_nutrition.html', {'upz_list': upz_list})


def get_wfp_nutrition_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_wfp_nutrition( '" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/wfp_nutrition_table.html', {'dataset': dataset})


@login_required
def unicef_nutrition(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/unicef_nutrition.html', {'upz_list': upz_list})


def get_unicef_nutrition_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_unicef_nutrition( '" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/unicef_nutrition_table.html', {'dataset': dataset})


@login_required
def education_student(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/education_student.html', {'upz_list': upz_list})


def get_education_student_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_education_student( '" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/education_student_table.html', {'dataset': dataset})


@login_required
def education_teacher(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/education_teacher.html', {'upz_list': upz_list})


def get_education_teacher_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_education_teacher('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/education_teacher_table.html', {'dataset': dataset})


@login_required
def wash(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/wash.html', {'upz_list': upz_list})


def get_wash_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_wash('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    print(q)
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/wash_table.html', {'dataset': dataset})


@login_required
def agriculture_fdmn(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/agriculture_fdmn.html', {'upz_list': upz_list})


def get_agriculture_fdmn_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_agriculture_fdmn( '" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/agriculture_fdmn_table.html', {'dataset': dataset})


@login_required
def agriculture_host(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/agriculture_host.html', {'upz_list': upz_list})


def get_agriculture_host_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    village = get_code(request.POST.get('village'))
    union = get_code(request.POST.get('union'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_agriculture_community('" + start_date + "','" + end_date + "','"+upazila+"','"+union+"','"+village+"')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/agriculture_host_table.html', {'dataset': dataset})


@login_required
def cfs_fdmn(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/cfs_fdmn.html', {'upz_list': upz_list})


def get_cfs_fdmn_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_cfs_fdmn('" + start_date + "','" + end_date + "','"+upazila+"','"+branch+"','"+camp+"')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/cfs_fdmn_table.html', {'dataset': dataset})


@login_required
def cfs_host(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/cfs_host.html', {'upz_list': upz_list})


def get_cfs_host_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    village = get_code(request.POST.get('village'))
    union = get_code(request.POST.get('union'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_cfs_community('" + start_date + "','" + end_date + "','" + upazila + "','" + union + "','" + village + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/cfs_host_table.html', {'dataset': dataset})


@login_required
def cfs_summary(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/cfs_summary.html', {'upz_list': upz_list})


def get_cfs_summary_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q1 = "select * from  get_rpt_cfs_summary_1('" + start_date + "','" + end_date + "','"+upazila+"')"
    q2 = "select * from  get_rpt_cfs_summary_2('" + start_date + "','" + end_date + "','"+upazila+"')"
    q3 = "select * from  get_rpt_cfs_summary_3('" + start_date + "','" + end_date + "','"+upazila+"')"
    dataset_1 = __db_fetch_values_dict(q1)
    dataset_2 = __db_fetch_values_dict(q2)
    dataset_3 = __db_fetch_values_dict(q3)
    response_data = {'dataset_1': dataset_1, 'dataset_2': dataset_2, 'dataset_3': dataset_3}
    return HttpResponse(json.dumps(response_data), content_type="application/json")
    # return render(request, 'hcmp_report/cfs_summary_table.html', {'dataset_1': dataset_1,'dataset_2' : dataset_2,'dataset_3':dataset_3})


@login_required
def pss(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/pss.html', {'upz_list': upz_list})


def get_pss_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_pss('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/pss_table.html', {'dataset': dataset})


@login_required
def c4d(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/c4d.html', {'upz_list': upz_list})


def get_c4d_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_c4d('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/c4d_table.html', {'dataset': dataset})


@login_required
def gbv(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/gbv.html', {'upz_list': upz_list})


def get_gbv_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_gbv('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    print q
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/gbv_table.html', {'dataset': dataset})


"""
Emtious @ ******* Start
"""
@login_required
def activity_progress_report(request):
    sector_list = get_sector_list()
    upz_list = get_upazila_list()
    return render(request, 'hcmp_report/activity_progress_report.html', {'sector_list':sector_list,'upz_list': upz_list})


def get_activity_progress_report_table(request):
    sector = str(request.POST.get('sector'))
    upazila = str(request.POST.get('upazila'))
    union = str(request.POST.get('union'))
    date_upto = str(request.POST.get('date_upto'))
    camp = str(request.POST.get('camp'))
    if date_upto == "":
        date_upto = datetime.datetime.now().date()

    q = " select * from get_rpt_4w_nfi('"+str(sector)+"', '"+str(upazila)+"', '"+str(union)+"', '"+str(camp)+"', '"+str(date_upto)+"') "
    print q
    dataset = __db_fetch_values_dict(q)
    print(q)
    return render(request, 'hcmp_report/activity_progress_report_table.html' , {'dataset':dataset})



def get_upazila_list():
    q = "select id,name from upazila "
    upz_list = makeTableList(q)
    return upz_list


def get_union_list(request):
    upazila = request.POST.get('upazila')
    q = "select id,name from unions where upazila_id =" + str(upazila)
    list = makeTableList(q)
    jsonlist = json.dumps({'union_list': list}, default=decimal_date_default)
    return HttpResponse(jsonlist)


def get_camp_list(request):
    union = request.POST.get('union')
    q = "select code,name from camp where union_id = " + str(union)
    list = makeTableList(q)
    jsonlist = json.dumps({'camp_list': list}, default=decimal_date_default)
    return HttpResponse(jsonlist)



def sector(request):
    return render(request, 'hcmp_report/sector.html',)


def create_sector(request):
    return HttpResponseRedirect('/hcmp_report/sector/')

"""
Emtious @ ******* End
"""



@login_required
def nfi_fdmn(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/nfi_fdmn.html', {'upz_list': upz_list})


def get_nfi_fdmn_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_shelter_nfi('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/nfi_fdmn_table.html', {'dataset': dataset})


@login_required
def nfi_host(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/nfi_host.html', {'upz_list': upz_list})


def get_nfi_host_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    village = get_code(request.POST.get('village'))
    union = get_code(request.POST.get('union'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_shelter_community('" + start_date + "','" + end_date + "','" + upazila + "','" + union + "','" + village + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/nfi_host_table.html', {'dataset': dataset})


@login_required
def drr_nfi(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/drr_nfi.html', {'upz_list': upz_list})


def get_drr_nfi_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_drr_shelter('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/drr_nfi_table.html', {'dataset': dataset})


@login_required
def drr_wash(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/drr_wash.html', {'upz_list': upz_list})


def get_drr_wash_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_rpt_drr_wash('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/drr_wash_table.html', {'dataset': dataset})


@login_required
def training(request):
    return render(request, 'hcmp_report/training.html', {'SECTOR_LIST': SECTOR_LIST})


def get_training_data_table(request):
    date_range = request.POST.get('date_range')
    sector = request.POST.get('sector')
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select *,(select value_label from xform_extracted where xform_id=592 and field_name='sector' and value_text=sector) as sector_name from vw_training where sector::text like '" + str(
        sector) + "' and date(date) between '" + start_date + "' and '" + end_date + "' "
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/training_table.html', {'dataset': dataset})


@login_required
def site_management(request):
    upz_list = get_upz_list()
    return render(request, 'hcmp_report/site_management.html', {'upz_list': upz_list})


def get_site_management_data_table(request):
    date_range = request.POST.get('date_range')
    upazila = get_code(request.POST.get('upazila'))
    branch = get_branch_code(request.POST.get('branch'))
    camp = get_camp_code(request.POST.get('camp'))
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select * from get_site_management('" + start_date + "','" + end_date + "','" + upazila + "','" + branch + "','" + camp + "')"
    dataset = __db_fetch_values_dict(q)
    return HttpResponse(json.dumps(dataset), content_type="application/json")

    # return render(request, 'hcmp_report/site_management_table.html', {'dataset': dataset})


@login_required
def meeting(request):
    return render(request, 'hcmp_report/meeting.html', {'SECTOR_LIST': SECTOR_LIST})


def get_meeting_data_table(request):
    date_range = request.POST.get('date_range')
    sector = request.POST.get('sector')
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select json,json->>'date' as meeting_date,json->>'meeting_type' as meeting_type,json->>'sector' as sector,(select value_label from xform_extracted where xform_id=588 and field_name='sector' and value_text=json->>'sector') as sector_name,(select value_label from xform_extracted where xform_id=588 and field_name='donor' and value_text=json->>'donor' ) as donor_name,json->>'meeting_summary' as meeting_summary ,json->>'meeting_doc' as uploaded_file from logger_instance where xform_id = (select id from logger_xform where id_string ='meeting') and deleted_at is null and Date(json->>'date') between '" + start_date + "' and '" + end_date + "' and (json->>'sector')::text like '" + str(
        sector) + "'"
    dataset = __db_fetch_values_dict(q)
    form_owner = __db_fetch_single_value(
        "select (select username from auth_user where id  = user_id) as form_owner from logger_xform where id_string= 'meeting' limit 1 ")
    return render(request, 'hcmp_report/meeting_table.html', {'dataset': dataset,'form_owner' :form_owner})


@login_required
def visitor(request):
    return render(request, 'hcmp_report/visitor.html')


def get_visitor_data_table(request):
    date_range = request.POST.get('date_range')
    if date_range == '':
        start_date = '01/01/2010'
        end_date = '12/28/2021'
    else:
        dates = get_dates(str(date_range))
        start_date = dates.get('start_date')
        end_date = dates.get('end_date')
    q = "select json->>'date' as visit_date,json->>'visitor_name' as visitor_name,json->>'visit_purpose' as visit_purpose,(select value_label from xform_extracted where xform_id=594 and field_name='donor' and value_text=json->>'donor') as donor_name from logger_instance where xform_id = (select id from logger_xform where id_string ='visitor') and deleted_at is null and Date(json->>'date') between '" + start_date + "' and '" + end_date + "' "
    dataset = __db_fetch_values_dict(q)
    return render(request, 'hcmp_report/visitor_table.html', {'dataset': dataset})


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
    camp_list = __db_fetch_values_dict(
        "select id,row_number() OVER () as serial_no,name,code,(select name from branch where id = branch_id) as branch from camp")
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
def get_geolocation_csv(request, id_string):
    both = ['cfs', 'shelter_nfi', 'agri_evironement']
    notapp = ['visitor', 'training', 'meeting']
    filenames = []

    if id_string not in notapp:
        geolocation_data = __db_fetch_values(
            "select(select field_name from geo_data where id = (select field_parent_id from geo_data where id = gd.field_parent_id)) as upazila_label, (select field_parent_id from geo_data where id = gd.field_parent_id) as upazila, (select field_name from geo_data where id = gd.field_parent_id limit 1) as union_name_label, gd.field_parent_id as union_name, field_name as village_label, id as village from geo_data gd where field_type_id = 92")
        branch_camp_data = __db_fetch_values(
            "SELECT(SELECT field_name FROM geo_data WHERE id = upazila_id) AS upazila_label, upazila_id as upazila, branch.name AS branch_label, branch.code as branch, camp.name AS camp_label, camp.code AS camp FROM camp LEFT JOIN branch ON branch.id = camp.branch_id")
        try:
            os.stat("onadata/media/geodata/" + str(id_string) + "/")
        except:
            os.mkdir("onadata/media/geodata/" + str(id_string) + "/")

        if id_string in both:
            f_path = os.path.join(settings.MEDIA_ROOT, "geodata/" + str(id_string) + "/village.csv")
            with open(f_path, 'w') as outfile:
                writer = csv.writer(outfile)
                writer.writerow(
                    ['upazila_label', 'upazila', 'union_name_label', 'union_name', 'village_label', 'village'])
                for data in geolocation_data:
                    writer.writerow([data[0], data[1], data[2], data[3], data[4], data[5]])

            filenames.append(f_path)

        f2_path = os.path.join(settings.MEDIA_ROOT, "geodata/" + str(id_string) + "/camp.csv")

        with open(f2_path, 'w') as outfile2:
            writer2 = csv.writer(outfile2)
            writer2.writerow(['upazila_label', 'upazila', 'branch_label', 'branch', 'camp_label', 'camp'])
            for data in branch_camp_data:
                writer2.writerow([data[0], data[1], data[2], data[3], data[4], data[5]])

        filenames.append(f2_path)

        zip_subdir = os.path.join(settings.MEDIA_ROOT, "geodata/" + id_string + "/geolocations")
        zip_filename = "%s.zip" % zip_subdir
        zf = zipfile.ZipFile(zip_filename, "w")

        for fpath in filenames:
            if os.path.exists(fpath):
                fdir, fname = os.path.split(fpath)
                zf.write(fpath, fname, zipfile.ZIP_DEFLATED)

        zf.close()

        resp = {
            'module_name': id_string,
            # 'csv_url': "http://"+request.META['HTTP_HOST'] + "/media/geodata/" + str(id_string) + "/geolocations.zip"
            'csv_url': "http://" + request.META['HTTP_HOST'] + "/media/geodata/" + str(id_string) + "/geolocations.zip"
        }

    else:
        resp = {
            'module_name': id_string,
            'csv_url': None
        }

    return HttpResponse(json.dumps(resp))



'''

        CONFIGURATION

'''

@csrf_exempt
@login_required
def sector_list(request):
    query = "SELECT id,sector_name, contact_focal_point, email, phone_no FROM public.sector order by id asc;"
    sector_list = json.dumps(__db_fetch_values_dict(query))
    return render(request, 'hcmp_report/sector_list.html', {
       'sector_list': sector_list
    })



@csrf_exempt
@login_required
def project(request,sector_id):
    q = "select id,name  from donor"
    df = pandas.DataFrame()
    df = pandas.read_sql(q, connection)
    donor_id = df.id.tolist()
    donor_name = df.name.tolist()
    donor_list = zip(donor_id, donor_name)
    if request.POST:
        donor_id = request.POST.get('donor')
        code = request.POST.get('code')
        insert_query = "INSERT INTO public.project(donor_id, sector_id, code) VALUES(" + str(
            donor_id) + ", " + str(sector_id) + ", '" + str(code) + "')"
        __db_commit_query(insert_query)
        return HttpResponse(json.dumps("ok"))
    sector_name = __db_fetch_single_value("select sector_name from sector where id = "+str(sector_id))
    return render(request, 'hcmp_report/project.html',
                 { 'donor_list': donor_list,'sector_id' : sector_id,'sector_name' : sector_name})





@login_required
def get_project(request,sector_id):
    q = "select id,(select name from donor where id = donor_id) donor,code from project where sector_id =" + str(sector_id)
    data = __db_fetch_values_dict(q)
    data_list = []
    data_dict = {}
    for tmp in data:
        data_dict['id'] = tmp['id']
        data_dict['donor'] = tmp['donor']
        data_dict['code'] = tmp['code']
        data_list.append(data_dict.copy())
        data_dict.clear()

    return render(request, "hcmp_report/project_datalist.html", {'dataset': data_list})



@csrf_exempt
@login_required
def activity_list(request,sector_id):
    query = "select row_number() over (order by id) as serial_number,activity_name,id,code from activity where sector_id = "+str(sector_id)
    activity_list = json.dumps(__db_fetch_values_dict(query))
    sector_name = __db_fetch_single_value("select sector_name from sector where id = "+str(sector_id))
    return render(request, 'hcmp_report/activity_list.html',
                 { 'activity_list': activity_list,'sector_id' : sector_id,'sector_name' : sector_name})




@csrf_exempt
@login_required
def add_activity(request,sector_id):
    code = __db_fetch_single_value("select coalesce(max(code),0) from activity") + 1
    sector_name = __db_fetch_single_value("select sector_name from sector where id = " + str(sector_id))

    if request.POST:
        activity_name = request.POST.get('name')
        activity_code = request.POST.get('code')
        data = __db_fetch_values_dict(
            "select code from activity where  code = " + str(activity_code))
        if len(data) == 0:
            insert_query = "INSERT INTO public.activity(id,activity_name, sector_id,code) VALUES(DEFAULT ,'" + str(
                activity_name) + "', " + str(sector_id) + ",'"+str(activity_code)+"')"
            __db_commit_query(insert_query)
            return HttpResponseRedirect("/hcmp_report/activity-list/"+str(sector_id))

    return render(request, 'hcmp_report/add_activity.html',
                 { 'sector_id' : sector_id,'sector_name' : sector_name,'code' : code})



@csrf_exempt
def check_duplicate_activity_code(request):
    activity_code = request.POST.get('code')
    sector_id = request.POST.get('sector_id')
    data = __db_fetch_values_dict("select code from activity where code = "+str(activity_code))
    if len(data) == 0:
        flag = 1
    else:
        flag = 0
    return HttpResponse(flag)


@csrf_exempt
@login_required
def subactivity_list(request,activity_id):
    query = "select row_number() over (order by id) as serial_number,sub_activity_name,id,code from sub_activity where activity_id = " + str(
        activity_id)
    subactivity_list = json.dumps(__db_fetch_values_dict(query))
    q = "select activity_name,(select sector_name from sector where id =sector_id) sector from activity where id = "+str(activity_id)
    data = __db_fetch_values_dict(q)
    for temp in data:
        data_dict = {
            'subactivity_list' : subactivity_list,'activity_name' : temp['activity_name'],'sector' : temp['sector'],'activity_id' :activity_id
        }
    return render(request, 'hcmp_report/subactivity_list.html',data_dict)



@csrf_exempt
@login_required
def add_subactivity(request,activity_id):
    sub_code = __db_fetch_single_value("select coalesce(max(code),0) from sub_activity where activity_id=" + activity_id) + 1
    activity_name= __db_fetch_single_value("select activity_name from activity where id = " + str(activity_id))
    sector_name = __db_fetch_single_value("select sector_name from sector where id = (select sector_id from activity where id = " + str(activity_id)+")")

    qry = "select id,unit_name from sub_activity_units"
    df = pandas.DataFrame()
    df = pandas.read_sql(qry,connection)
    unit = zip(df.id.tolist(),df.unit_name.tolist())

    if request.POST:
        subactivity_name = request.POST.get('name')
        code = request.POST.get('code')
        unit = request.POST.get('unit')
        data = __db_fetch_values_dict(
            "select code from sub_activity where activity_id = " + str(activity_id) + "  and code = " + str(code))
        if len(data) == 0:
            insert_query = "INSERT INTO public.sub_activity(id,sub_activity_name, code,activity_id,unit_id) VALUES(DEFAULT ,'" + str(
                subactivity_name) + "', " + str(code) + ","+str(activity_id)+","+str(unit)+")"
            __db_commit_query(insert_query)
        return HttpResponseRedirect("/hcmp_report/subactivity_list/"+str(activity_id))

    return render(request, 'hcmp_report/add_subactivity.html',
                 { 'activity_id' : activity_id,'activity_name' : activity_name,'sector_name' : sector_name,'code' : sub_code,'unit':unit})


@csrf_exempt
def check_duplicate_sub_activity_code(request):
    code = request.POST.get('code')
    activity_id = request.POST.get('activity_id')
    data = __db_fetch_values_dict("select code from sub_activity where activity_id = "+str(activity_id)+"  and code = "+str(code))
    if len(data) == 0:
        flag = 1
    else:
        flag = 0
    return HttpResponse(flag)




@csrf_exempt
@login_required
def activity_map_list(request,subactivity_id):
    query = "select id,row_number() over (order by id) as serial_number,((select name from donor where id = (select donor_id from project where id = project_id) )||'-' ||((select code from project where id = project_id))) project,id,Date(start_date) start_date,Date(end_date) end_date, target,status from activity_mapping where sub_activity_id = " + str(
        subactivity_id)
    mapping_list = json.dumps(__db_fetch_values_dict(query), default=decimal_date_default)
    data_dict = get_sub_activity_info(subactivity_id)
    data = {
        'sub_activity': data_dict.get('sub_activity_name'), 'activity': data_dict.get('activity'),'subactivity_id': subactivity_id,
        'sector': data_dict.get('sector'), 'mapping_list': mapping_list
    }
    return render(request, 'hcmp_report/activity_map_list.html',data)


@csrf_exempt
@login_required
def add_activity_map(request,subactivity_id):
    data_dict = get_sub_activity_info(subactivity_id)

    sector_id = data_dict.get('sector_id')
    q = "select id,((select name from donor where id = donor_id) ||'-'||code) donor_project from project where sector_id = "+str(sector_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(q, connection)
    project_id = df.id.tolist()
    donor_name = df.donor_project.tolist()
    project_list = zip(project_id, donor_name)

    query = "select project_id,to_char(start_date::date,'yyyy-mm-dd') start_date,to_char(end_date::date,'yyyy-mm-dd') end_date from activity_mapping where  sub_activity_id = " + str(subactivity_id)
    v_dat = __db_fetch_values_dict(query)
    validate_dict = {}
    for each in v_dat:
        validate_dict[each['project_id']] = {'start_date':each['start_date'],'end_date':each['end_date']}


    data = {
       'validate_dict':json.dumps(validate_dict), 'sub_activity' : data_dict.get('sub_activity_name'),'activity' : data_dict.get('activity'),'sector' : data_dict.get('sector'),'project_list' :project_list,'subactivity_id' : subactivity_id
    }

    if request.POST:
        project_id = request.POST.get('project_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        target = request.POST.get('target')
        target_population = request.POST.get('target_population')
        camp = request.POST.get('camp')
        union = request.POST.get('union')
        upazila = request.POST.get('upazila')
        border_transit_location = request.POST.get('border_transit_location')
        status = request.POST.get('status')
        if target_population in [11,12,13]:
            camp = ''


        insert_query = "INSERT INTO public.activity_mapping(id, project_id, start_date, end_date, target, sub_activity_id,upazila,union_name,camp,border_transit_location,status,target_population)VALUES (DEFAULT , "+str(project_id)+", '"+start_date+"', '"+end_date+"', "+str(target)+", "+str(subactivity_id)+",'"+str(upazila)+"','"+str(union)+"','"+str(camp)+"','"+str(border_transit_location)+"','"+str(status)+"','"+str(target_population)+"')"
        __db_commit_query(insert_query)
        return HttpResponseRedirect("/hcmp_report/activity-map-list/"+str(subactivity_id))

    return render(request, 'hcmp_report/add_activity_map.html',data)


def edit_activity_map(request,subactivity_id,id):
    if request.POST:
        id = request.POST.get('id')
        project_id = request.POST.get('project_id')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        target = request.POST.get('target')
        target_population = request.POST.get('target_population')
        camp = request.POST.get('camp')
        union = request.POST.get('union')
        upazila = request.POST.get('upazila')
        border_transit_location = request.POST.get('border_transit_location')
        status = request.POST.get('status')
        if target_population in [11, 12, 13]:
            camp = ''

        update_query = "UPDATE public.activity_mapping SET project_id="+str(project_id)+", start_date='"+str(start_date)+"', end_date='"+str(end_date)+"', target="+str(target)+", target_population='"+str(target_population)+"', upazila='"+str(upazila)+"', union_name='"+str(union)+"', camp='"+str(camp)+"', border_transit_location='"+str(border_transit_location)+"', status='"+str(status)+"' WHERE id="+str(id)
        __db_commit_query(update_query)
        return HttpResponseRedirect("/hcmp_report/activity-map-list/" + str(subactivity_id))
    data_dict = get_sub_activity_info(subactivity_id)

    sector_id = data_dict.get('sector_id')
    q = "select id,((select name from donor where id = donor_id) ||'-'||code) donor_project from project where sector_id = " + str(
        sector_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(q, connection)
    project_id = df.id.tolist()
    donor_name = df.donor_project.tolist()
    project_list = zip(project_id, donor_name)

    query = "select project_id,to_char(start_date::date,'yyyy-mm-dd') start_date,to_char(end_date::date,'yyyy-mm-dd') end_date from activity_mapping where  sub_activity_id = " + str(
        subactivity_id)
    v_dat = __db_fetch_values_dict(query)
    validate_dict = {}
    for each in v_dat:
        validate_dict[each['project_id']] = {'start_date': each['start_date'], 'end_date': each['end_date']}

    get_prev_data_query = "SELECT o.id,o.created_at,o.updated_at,o.project_id,o.target,o.sub_activity_id,o.target_population,o.upazila,o.union_name,o.camp,o.border_transit_location,o.status,start_date::date,end_date::date FROM activity_mapping as o where id = "+str(id)
    df = pandas.DataFrame()
    df = pandas.read_sql(get_prev_data_query, connection)
    project_id = df.project_id.tolist()[0]
    start_date = df.start_date.tolist()[0]
    end_date = df.end_date.tolist()[0]
    target = df.target.tolist()[0]
    status = df.status.tolist()[0]
    target_population = df.target_population.tolist()[0]
    camp = df.camp.tolist()[0]
    union = df.union_name.tolist()[0]
    upazila = df.upazila.tolist()[0]
    # upz_name = df.upz_name.tolist()[0]
    border_transit_location = df.border_transit_location.tolist()[0]

    set_qry = "select code id,name from upazila "
    set_upz = json.dumps(__db_fetch_values_dict(set_qry))

    if upazila == '' or upazila is None:
        set_qry = "select code id,name from unions"
    else:
        set_qry = "select code id,name from unions where upazila_id = " + str(upazila)
    set_uni = json.dumps(__db_fetch_values_dict(set_qry))

    if union == '' or union is None:
        set_qry = "select code id,name from camp"
    else:
        set_qry = "select code id,name from camp where union_id = " + str(union)
    set_camp = json.dumps(__db_fetch_values_dict(set_qry))

    if upazila == '' or upazila is None:
        set_qry = "select code id,name from border_transit_location"
    else:
        set_qry = "select code id,name from border_transit_location where upazila_id = " + str(upazila)
    set_border = json.dumps(__db_fetch_values_dict(set_qry))

    data = {
        'validate_dict': json.dumps(validate_dict), 'sub_activity': data_dict.get('sub_activity_name'),
        'activity': data_dict.get('activity'), 'sector': data_dict.get('sector'), 'project_list': project_list,
        'subactivity_id': subactivity_id
        ,'prev_project_id' : project_id
        ,'start_date' : start_date
        ,'end_date' : end_date
        ,'target' : target
        ,'status' : status
        ,'target_population': target_population
        ,'camp' : camp
        ,'union' : union
        ,'upazila' : upazila
        ,'border_transit_location' : border_transit_location
        ,'set_upz':set_upz
        ,'set_uni':set_uni
        ,'set_camp':set_camp
        ,'set_border':set_border
        ,'id':id
    }



    return render(request, 'hcmp_report/edit_activity_map.html', data)

def get_sub_activity_info(sub_activity_id):
    q = "select  id,sub_activity_name,(select activity_name from activity where id  = activity_id) activity, (select sector_name from sector where id = (select sector_id from activity where id = sub_activity.activity_id)) sector,(select id from sector where id = (select sector_id from activity where id = sub_activity.activity_id)) sector_id from sub_activity where id = "+str(sub_activity_id)
    #print q
    data = __db_fetch_values_dict(q)
    #print data
    data_dict = {}
    for temp in data:
        data_dict = {
            'sub_activity_name' : temp['sub_activity_name'],'activity' : temp['activity'],'sector' : temp['sector'],'sector_id' :temp['sector_id']
        }
    return data_dict


def shelter_nfi_daily_report(request):
    from_date = datetime.datetime.today().date()
    return render(request, 'hcmp_report/shelter_nfi_daily_report.html',{'from_date':from_date})

@csrf_exempt
def get_report_shelter_nfi_daily_report(request):
    search_date = request.POST.get('search_date')
    target_population = request.POST.get('target_population')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    camp = request.POST.get('camp')
    border_transit_location = request.POST.get('border_transit_location')
    section = request.POST.get('section')
    query = """select rserial_no,coalesce(ract_name,'') ract_name,coalesce(runit,'') runit,coalesce(rday_cnt,0) rday_cnt,coalesce(rmonth_cnt,0) rmonth_cnt,coalesce(rtotal,0) rtotal from get_rpt_shelter_nfi_day('""" +str(search_date)+ """', '"""+str(upazila)+"""','"""+str(union)+"""','"""+str(camp)+"""','"""+str(border_transit_location)+"""','"""+str(target_population)+"""','"""+str(section)+"""')"""
    print(query)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


def site_improvement_report(request):
    from_date = datetime.datetime.today().date()
    return render(request, 'hcmp_report/site_improvement_report.html',{'from_date':from_date})

@csrf_exempt
def get_site_improvement_report(request):
    search_date = request.POST.get('search_date')
    upazila = request.POST.get('upazila')
    union = request.POST.get('union')
    camp = request.POST.get('camp')
    query = """  with filtered_site_improvement as( select * from vwactivity_progress_site_improvement where upazila like '"""+str(upazila)+"""' and union_name like '"""+str(union)+"""' and camp like '"""+str(camp)+"""' and act_date::date between '-infinity'::date and '""" +str(search_date)+ """'), am as ( select (select sub_activity_code from vw_all_map where sub_activity_id = am.sub_activity_id limit 1),(select project_code from vw_all_map where project_id = am.project_id limit 1),start_date::date,end_date::date,status,upazila,union_name,camp,sum(target) s_target from activity_mapping am where upazila like '"""+str(upazila)+"""' and union_name like '"""+str(union)+"""' and camp like '"""+str(camp)+"""' group by sub_activity_id,project_id,start_date::date,end_date::date,status,upazila,union_name,camp )select act_level,implement_partner,am.camp,activity,sub_activity,'Meter' unit,s_target::text,trunc(sum(number::float)::numeric,2)::text num,start_date::text,end_date::text,trunc(sum(length::float)::numeric,2)::text len,status,case when s_target::bigint != 0 then trunc((sum(length::float)*100.0/s_target)::numeric,2)::text else '0' end  progress from filtered_site_improvement st,am where am.sub_activity_code::bigint = st.sub_activity::bigint and am.project_code::bigint = st.project_name::bigint and am.upazila = st.upazila and am.union_name = st.union_name and am.camp = st.camp group by act_level,implement_partner,am.camp,activity,sub_activity,s_target,start_date,end_date,status """
    print(query)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)


def shelter_nfi_monthly_report(request):
    from_date = datetime.datetime.today().date()
    q_donor = "select id,name from donor"
    df = pandas.DataFrame()
    df = pandas.read_sql(q_donor,connection)
    donor = zip(df.id.tolist(),df.name.tolist())
    return render(request, 'hcmp_report/shelter_nfi_monthly_report.html', {'from_date': from_date,'donor':donor})


@csrf_exempt
def get_report_shelter_nfi_monthly_report(request):
    search_date = request.POST.get('search_date')
    donor = request.POST.get('donor')
    section = request.POST.get('section')
    query = """ select rserial_no,coalesce(ract_name,'') ract_name,coalesce(runit,'') runit,coalesce(rcur_mon_cnt,0)::text rcur_mon_cnt,coalesce(rupto_last_month_cnt,0)::text rupto_last_month_cnt,coalesce(rtotal,0)::text rtotal,coalesce(rtarget::text,'') rtarget,case when rtarget is null then '-1' when rtarget::int = 0 then '0' else trunc((rtotal::numeric/rtarget::numeric)*100,2)::text end || ' %' as percentage  from get_rpt_shelter_nfi_month('"""+str(search_date)+"""', '"""+str(donor)+"""','"""+str(section)+"""') """
    print(query)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@login_required
def hcmp_dashboard(request):
    return render(request, 'hcmp_report/hcmp_dashboard_f_1.html')

@login_required
def forms_configuation(request,tiles_id):
    username = request.user
    query = "select * from tiles where id = "+str(tiles_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    if not df.empty:
        tiles_name = df.tiles_name.tolist()[0]
        icon_path = df.icon_path.tolist()[0]
        return render(request,'hcmp_report/hcmp_dashboard_f_2.html',{'tiles_id':tiles_id,'tiles_name':tiles_name,'icon_path':icon_path})
    return render(request,'hcmp_report/hcmp_dashboard_f_2.html',{'tiles_id':'','tiles_name':'','icon_path':''})


@csrf_exempt
def get_forms_list(request):
    username = request.user
    user_id = request.user.id
    tiles_id = request.POST.get('tiles_id')
    query = """ select '<div class="col-md-6"><div class="portlet solid" style="background-color: ghostwhite"> <div class="portlet-title"> <div class="caption"> <i class="fa fa-forumbee"></i>'|| (select title from logger_xform where id = form_id::int limit 1) ||'</div> </div> <div class="portlet-body"> <div class="actions"> <a href="/usermodule/brac_admin/projects-views/' || (select id_string from logger_xform where id = form_id::int limit 1) || '/" class="btn red btn-md" style="margin-right: 3px;"> <i class="fa fa-briefcase" aria-hidden="true"></i> Details </a>' || case when (select user_id from logger_xform where id = form_id::int limit 1) = """+str(user_id)+""" then '<a href="/""" + str(username) + """/forms/' || (select id_string from logger_xform where id = form_id::int limit 1) || '/settings" class="btn red btn-md"> <i class="fa fa-cogs" aria-hidden="true"></i> Settings </a> <a href="/usermodule/""" + str(username) + """/forms/' || (select id_string from logger_xform where id = form_id::int limit 1) || '/role_form_map" class="btn red btn-md"> <i class="fa fa-users" aria-hidden="true"></i> Permissions </a><a href="/hcmp_report/form_new_submission/'||(SELECT id_string FROM   logger_xform WHERE  id = form_id::int limit 1) || '/" class="btn red btn-md" style="margin-left:3px !important;"> <i class="fa fa-plus" aria-hidden="true"></i> New Submission</a>' else ''  end  || ' </div> </div> </div> </div>' as html from tiles_sector_form_map where tiles_id::int = """+str(tiles_id)
    df = pandas.read_sql(query,connection)
    main_str = ""
    for each in df['html']:
        main_str += str(each)
    main_str = json.dumps({'main_str':main_str})
    return HttpResponse(main_str)

@csrf_exempt
def get_settings(request):
    tiles_id = request.POST.get('tiles_id')
    # href = ""
    # onclick = "delete_entity(this,' || sector_id ||')"
    # href="#" data-href="/hcmp_report/delete_sector/'|| sector_id ||'/"""+str(tiles_id)+""""
    query = """ SELECT '<div class="col-md-6"> <div class="portlet box" style="background-color: deeppink"> <div class="portlet-title"> <div class="caption" ><i class="fa fa-paper-plane" style="color: ghostwhite"></i>' ||( SELECT sector_name FROM sector WHERE id = sector_id::int limit 1) ||' </div> <div class="actions"><a href="/hcmp_report/project/' || sector_id ||'" class="btn red btn-md settings_btn"> Donor </a> <a href="/hcmp_report/activity-list/' || sector_id ||'" class="btn red btn-md settings_btn"> Activity </a> <a  href="/hcmp_report/edit_sector/'|| sector_id ||'/""" +str(tiles_id)+ """" class="btn red btn-md settings_btn">Edit </a> <a  class="btn red btn-md settings_btn delete-item" data-toggle="modal" data-target="#confirm-delete" data-original-title="Delete" onclick = "delete_entity(this,' || sector_id ||')"  >Delete </a></div> </div> <div class="portlet-body"> <ul class="list-group" style="text-align: left"> <li class="list-group-item"><span class="focal_span">Contact Focal Point:</span><span>' || ( SELECT contact_focal_point FROM sector WHERE id = sector_id::int limit 1) || '</span></li> <li class="list-group-item"><span class="phone_span">Phone No:</span><span>' || ( SELECT phone_no FROM sector WHERE id = sector_id::int limit 1) || '</span></li> <li class="list-group-item"><span class="email_span">Email:</span><span>' || ( SELECT email FROM sector WHERE id = sector_id::int limit 1) || '</span></li> </ul> </div> </div> </div>' AS html FROM tiles_sector_form_map WHERE tiles_id::int = """ + str(tiles_id)
    df = pandas.read_sql(query, connection)
    main_str = ""
    for each in df['html']:
        main_str += str(each)
    main_str = json.dumps({'main_str': main_str})
    return HttpResponse(main_str)

@login_required
def edit_sector(request,sector_id,tiles_id):
    if request.POST:
        tiles_id = request.POST.get('tiles_id')
        sector_id = request.POST.get('sector_id')
        sector_name = request.POST.get('sector_name')
        contact_focal_point = request.POST.get('contact_focal_point')
        email = request.POST.get('email')
        phone_no = request.POST.get('phone_no')
        update_qry = "update sector set sector_name = '"+str(sector_name)+"',contact_focal_point = '"+str(contact_focal_point)+"', email = '"+str(email)+"', phone_no='"+str(phone_no)+"' where id = "+str(sector_id)
        __db_commit_query(update_qry)
        return HttpResponseRedirect('/hcmp_report/forms_configuation/'+str(tiles_id)+'/')
    qry = "select * from sector where id = "+str(sector_id)
    df = pandas.DataFrame()
    df = pandas.read_sql(qry,connection)
    sector_name = df.sector_name.tolist()[0]
    contact_focal_point = df.contact_focal_point.tolist()[0]
    email = df.email.tolist()[0]
    phone_no = df.phone_no.tolist()[0]
    return render(request,'hcmp_report/edit_sector.html',{
        'tiles_id':tiles_id,
        'sector_id':sector_id,
        'sector_name':sector_name,
        'contact_focal_point':contact_focal_point,
        'email':email,
        'phone_no':phone_no
    })


def delete_sector(request,sector_id,tiles_id):
    del_qry = "delete from sector where id = "+str(sector_id)
    __db_commit_query(del_qry)
    del_qry = "delete from tiles_sector_form_map where sector_id::int = " + str(sector_id) +" and tiles_id::int = "+str(tiles_id)
    __db_commit_query(del_qry)
    return HttpResponseRedirect('/hcmp_report/forms_configuation/' + str(tiles_id) + '/')





"""
    API
"""

def get_activity_csv(request,id_string):
    if id_string == 'activity_progress_nfi':
        sector_id = 1
    if id_string == 'activity_progress_shelter':
        sector_id = 2
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    if id_string == 'activity_progress_site_improvement':
        sector_id = 11


    #q = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 as (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 as (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 as (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT DISTINCT t4.donor_name donor_label, t4.donor_code::text donor, t3.activity_name activity_label, t4.donor_code ||t3.activity_code activity, t3.sub_activity_name subactivity_label, t4.donor_code||t3.activity_code||t3.sub_activity_code sub_activity FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id"
    q= "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT t4.donor_name donor_label, t4.donor_code::text donor, t3.activity_name activity_label, t4.donor_code ||t3.activity_code activity, t3.sub_activity_name subactivity_label, t4.donor_code||t3.activity_code||t3.sub_activity_code sub_activity,t4.donor_name||'-'||t4.project_code project_label,t4.donor_code||t3.activity_code||t3.sub_activity_code||t4.project_code project FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id "
    print q
    df = pandas.read_sql(q, connection)
    #print df
    file_name = 'act' + '.csv'
    file_path = 'onadata/media/forms/'+id_string+'/'
    file  = file_path+file_name

    if not os.path.exists(file_path):
        os.makedirs(file_path)

    df.to_csv(file, encoding='utf-8',index=False)
    # Folder name in ZIP archive which contains the above files
    # E.g [thearchive.zip]/somefiles/file2.txt
    zip_subdir = "itemsetfiles"
    zip_filename = "%s.zip" % zip_subdir
    # Open StringIO to grab in-memory ZIP contents
    s = StringIO.StringIO()
    # The zip compressor
    zf = zipfile.ZipFile(s, "w")

    # Add file, at correct path
    zf.write(file, file_name)

    # Must close zip for all contents to be written
    zf.close()
    # Grab ZIP file from in-memory, make response with correct MIME-type
    resp = HttpResponse(s.getvalue(), mimetype="application/x-zip-compressed")
    # ..and correct content-disposition
    resp['Content-Disposition'] = 'attachment; filename=%s' % zip_filename

    return resp



#Custom export for HCMP Reporting
@csrf_exempt
def get_export(request):
    end_date = request.POST.get('end_date')
    id_string = request.POST.get('f_id')
    if id_string == 'activity_progress_nfi':
        sector_id = 1
    if id_string == 'activity_progress_shelter':
        sector_id = 2
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    q = " select * from get_rpt_4w_nfi('" + str(sector_id) + "', '%', '%', '%', '" + str(end_date) + "') "
    print q
    main_df = pd.read_sql(q, connection)

    columns = ['r_start_date', 'r_end_date','r_last_update_date','r_activity_status','r_total_planned_households','r_reached_total_male','r_reached_total_female','r_total_adult_females','r_total_adult_males','r_total_child_females','r_total_child_males','r_zone','r_focal_point','r_mobile','r_email']
    main_df.drop(columns, inplace=True, axis=1)
    # changing cols with rename()
    main_df = main_df.rename(columns={"r_sl": "Serial",
                                    "r_program_partner": "Program Partner",
                                    "r_implement_partner": "Implement partner",
                                      "r_response": "Response",
                                      "r_donor": "Donor",
                                      "r_act_activity": "Activity",
                                      "r_act_sub_activity": "Sub Activity",
                                      "r_act_cash_in_hand": "cash/in kind",
                                      "r_act_activity_details": "Activity Details",
                                      "r_act_unit_per_hh": "Activity Unit per hh",
                                      "r_act_reached_total_hh": "Activity reached total hh",
                                      "r_act_reached_total_beneficiaries": "Total beneficiaries",
                                      "r_submission_date": "Activity date",
                                      "r_district": "District",
                                      "r_upazila": "Upazila",
                                      "r_union_name": "Union",
                                      "r_camp": "Camp",
                                      "r_zone": "Zone",
                                      "r_target_population": "Target population",
                                      "r_act_remarks": "Activity Remarks"})


    millis = int(round(time.time() * 1000))
    file_name = id_string + str(millis) + '.xls'
    path = 'media/exported_files/' + file_name
    file_path = '/home/hcmp/src_hcmp_rpt/kobocat/onadata/' + path
    writer = ExcelWriter(file_path, engine='xlwt')
    main_df.to_excel(writer, 'sheet1', index=False)
    writer.save()
    print file_path

    return HttpResponse(path)

def multipleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchall()
    cursor.close()
    return value

def singleValuedQuryExecution(query):
    cursor = connection.cursor()
    cursor.execute(query)
    value = cursor.fetchone()
    cursor.close()
    return value

@login_required
def donor(request):
    queryDonorNameList = 'select id,name donor_name from donor order by id'
    donorNameList = multipleValuedQuryExecution(queryDonorNameList)
    jsonDonorNameList = json.dumps({'donorNameList': donorNameList}, default=decimal_date_default)

    content = {

        'jsonDonorNameList': jsonDonorNameList
    }
    print(content)

    return render(request, 'hcmp_report/donor.html', content)


@login_required
def donorCreate(request):
    username = request.user.username
    donorName = request.POST.get('donor_name', '')
    isEdit = request.POST.get('isEdit')

    if isEdit != '':
        queryEditDonorName = "UPDATE public.donor SET name='" + donorName + "' WHERE id= " + isEdit
        __db_commit_query(queryEditDonorName)  ## Query Execution Function
    else:
        queryCreateDonorName = "INSERT INTO public.donor (id, name, created_at,  updated_at)VALUES(nextval('donor_id_seq'::regclass),'" + str(
            donorName) + "', now(), now())"
        __db_commit_query(queryCreateDonorName)  ## Query Execution Function

    return HttpResponseRedirect('/hcmp_report/donor/')


@login_required
def donor_Edit(request):
    id = request.POST.get('id')
    queryFetchSpecificDonor = " SELECT id,name FROM public.donor where id = " + str(id)
    getFetchSpecificDonor = singleValuedQuryExecution(queryFetchSpecificDonor)

    jsonFetchSpecificDonor = json.dumps({'getFetchSpecificDonor': getFetchSpecificDonor}, default=decimal_date_default)

    return HttpResponse(jsonFetchSpecificDonor)

@login_required
def donor_Delete(request,donor_id):
    del_query = "delete from donor where id ="+str(donor_id)
    __db_commit_query(del_query)
    return HttpResponseRedirect('/hcmp_report/donor/')

@csrf_exempt
def getUpazilas(request):
    query = "select code id,name from upazila"
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@csrf_exempt
def getUnions(request):
    upazila = request.POST.get('upz')
    query = "select code id,name from unions where upazila_id = "+str(upazila)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@csrf_exempt
def getCamp(request):
    camp = request.POST.get('camp')
    query = "select code id,name from camp where union_id = "+str(camp)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

@csrf_exempt
def get_border_transit_location(request):
    upazila = request.POST.get('upz')
    query = "select code id,name from border_transit_location where upazila_id = " + str(upazila)
    data = json.dumps(__db_fetch_values_dict(query))
    return HttpResponse(data)

def getActivityMapValidation(request):
    project_id = request.POST.get('project_id')
    subactivity_id = request.POST.get('subactivity_id')
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')

    query = "select to_char(start_date::date,'yyyy-mm-dd') start_date,to_char(end_date::date,'yyyy-mm-dd') end_date from activity_mapping where project_id = "+str(project_id)+" and sub_activity_id = "+str(subactivity_id)+" "
    df = pandas.DataFrame()
    df = pandas.read_sql(query,connection)
    stat = -1
    s_date = ''
    e_date = ''
    if df.empty:
        stat = 0
    else:
        stat = 1
        s_date = df.start_date.tolist()[0]
        e_date = df.end_date.tolist()[0]

    data ={
        'stat':stat,'s_date':s_date,'e_date':e_date
    }
    return HttpResponse(json.dumps(data))


@login_required
def form_new_submission(request,id_string):
    if id_string == 'activity_progress_nfi':
        sector_id = 1
        title = 'Activity Progress - NFI'
    if id_string == 'activity_progress_shelter':
        sector_id = 2
        title = 'Activity Progress-Shelter'
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    if id_string == 'activity_progress_site_improvement':
        title = 'Activity Progress-Site Improvement'
        sector_id = 11

    xform_id = __db_fetch_single_value("select id from logger_xform where id_string ='" + str(id_string) + "'")
    form_uuid = __db_fetch_single_value("select uuid from logger_xform where id = " + str(xform_id))
    username = request.user.username

    activity_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = " + str(
        sector_id) + ")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = " + str(
        sector_id) + "), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code ||t3.activity_code) activity , t3.activity_name activity_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_activity_list = json.dumps(__db_fetch_values_dict(activity_query))

    sub_activity_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = " + str(
        sector_id) + ")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = " + str(
        sector_id) + "), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code||t3.activity_code||t3.sub_activity_code) sub_activity, t3.sub_activity_name subactivity_label  FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_sub_activity_list = json.dumps(__db_fetch_values_dict(sub_activity_query))

    project_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = " + str(
        sector_id) + ")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = " + str(
        sector_id) + "), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code||t3.activity_code||t3.sub_activity_code||t4.project_code) project , t4.donor_name||'-'||t4.project_code project_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_project_list = json.dumps(__db_fetch_values_dict(project_query))

    doner_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = " + str(
        sector_id) + ")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = " + str(
        sector_id) + "), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code)::text donor , t4.donor_name donor_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_donor_list = json.dumps(__db_fetch_values_dict(doner_query))

    if id_string == 'activity_progress_site_improvement':
        return render(request, "hcmp_report/activity_progress_site_imporovement_edit.html",
                      {'id_string': id_string, 'xform_id': xform_id, 'username': username, 'title':title ,
                       'opt_donor_list': opt_donor_list,'opt_activity_list': opt_activity_list,
                       'opt_sub_activity_list': opt_sub_activity_list, 'opt_project_list': opt_project_list,
                       'form_uuid': form_uuid})
    else:
        return render(request, "hcmp_report/activity_progress_edit.html",
                  {'id_string': id_string, 'xform_id': xform_id, 'username': username,
                   'opt_donor_list': opt_donor_list, 'opt_activity_list': opt_activity_list, 'title': title,
                    'form_uuid': form_uuid,'opt_sub_activity_list': opt_sub_activity_list, 'opt_project_list': opt_project_list, 'instance_id': ''})


def activity_progress_edit(request, id_string , instance_id):

    #instance_id = 20165

    if id_string == 'activity_progress_nfi':
        sector_id = 1
        title = 'Activity Progress - NFI'
    if id_string == 'activity_progress_shelter':
        sector_id = 2
        title = 'Activity Progress-Shelter'
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    if id_string == 'activity_progress_site_improvement':
        title = 'Activity Progress-Site Improvement'
        sector_id = 11


    xform_id = __db_fetch_single_value("select id from logger_xform where id_string ='" + str(id_string) + "'")
    form_uuid = __db_fetch_single_value("select uuid from logger_xform where id = " + str(xform_id))
    xml_data = __db_fetch_single_value("select xml from logger_instance where id = " + str(instance_id))
    #xml_data = str(xml_data).replace('\t', '').replace('\n', '').replace("'","\\'")
    xml_data = smart_str(xml_data).replace('\t', '').replace('\n', '').replace("'", "\\'")

    username = request.user.username

    #
    # if id_string == 'activity_progress_nfi':
    #     sector_id = 1
    # if id_string == 'activity_progress_shelter':
    #     sector_id = 2
    # if id_string == 'activity_progress_c4d':
    #     sector_id = 2
    #

    #q = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 as (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 as (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 as (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT DISTINCT t4.donor_name donor_label, t4.donor_code::text donor, t3.activity_name activity_label, t4.donor_code ||t3.activity_code activity, t3.sub_activity_name subactivity_label, t4.donor_code||t3.activity_code||t3.sub_activity_code sub_activity FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id"
    #Previously Used
    # q= "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT t4.donor_name donor_label, t4.donor_code::text donor, t3.activity_name activity_label, t4.donor_code ||t3.activity_code activity, t3.sub_activity_name subactivity_label, t4.donor_code||t3.activity_code||t3.sub_activity_code sub_activity,t4.donor_name||'-'||t4.project_code project_label,t4.donor_code||t3.activity_code||t3.sub_activity_code||t4.project_code project FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "

    activity_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code ||t3.activity_code) activity , t3.activity_name activity_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_activity_list =  json.dumps(__db_fetch_values_dict(activity_query))


    sub_activity_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code||t3.activity_code||t3.sub_activity_code) sub_activity, t3.sub_activity_name subactivity_label  FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_sub_activity_list =  json.dumps(__db_fetch_values_dict(sub_activity_query))


    project_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code||t3.activity_code||t3.sub_activity_code||t4.project_code) project , t4.donor_name||'-'||t4.project_code project_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_project_list =  json.dumps(__db_fetch_values_dict(project_query))


    doner_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code)::text donor , t4.donor_name donor_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.sub_activity_id is not null "
    opt_donor_list =  json.dumps(__db_fetch_values_dict(doner_query))



    if id_string == 'activity_progress_site_improvement':
        return render(request, "hcmp_report/activity_progress_site_imporovement_edit.html",
                      {'id_string': id_string, 'xform_id': xform_id, 'username': username, 'title':title ,
                       'opt_donor_list': opt_donor_list,'opt_activity_list': opt_activity_list,
                       'opt_sub_activity_list': opt_sub_activity_list, 'opt_project_list': opt_project_list,
                       'form_uuid': form_uuid, 'xml_data': xml_data, 'instance_id': instance_id})

    else:
        return render(request, "hcmp_report/activity_progress_edit.html",
                          {'id_string': id_string, 'xform_id': xform_id, 'username': username,
                           'opt_donor_list': opt_donor_list, 'opt_activity_list': opt_activity_list, 'title':title ,
                           'opt_sub_activity_list': opt_sub_activity_list, 'opt_project_list': opt_project_list,
                           'form_uuid': form_uuid, 'xml_data': xml_data, 'instance_id': instance_id})

@csrf_exempt
def get_opt_activity_list(request , id_string  , donor):

    if id_string == 'activity_progress_nfi':
        sector_id = 1
    if id_string == 'activity_progress_shelter':
        sector_id = 2
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    if id_string == 'activity_progress_site_improvement':
        sector_id = 11

    activity_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code ||t3.activity_code) activity , t3.activity_name activity_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.donor_code::text like '"+ str(donor) + "' and t4.sub_activity_id is not null "
    opt_activity_list =  json.dumps(__db_fetch_values_dict(activity_query))

    return HttpResponse(opt_activity_list)

@csrf_exempt
def get_opt_sub_activity_list(request , id_string  , donor , activity ):

    if id_string == 'activity_progress_nfi':
        sector_id = 1
    if id_string == 'activity_progress_shelter':
        sector_id = 2
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    if id_string == 'activity_progress_site_improvement':
        sector_id = 11


    sub_activity_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code||t3.activity_code||t3.sub_activity_code) sub_activity, t3.sub_activity_name subactivity_label  FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.donor_code::text like '"+ str(donor) + "' and  t4.donor_code::text||t3.activity_code::text like '"+str(activity)+"' and  t4.sub_activity_id is not null "
    opt_sub_activity_list =  json.dumps(__db_fetch_values_dict(sub_activity_query))


    return HttpResponse(opt_sub_activity_list)


@csrf_exempt
def get_opt_project_list(request , id_string  , donor , activity , sub_activity  ):

    if id_string == 'activity_progress_nfi':
        sector_id = 1
    if id_string == 'activity_progress_shelter':
        sector_id = 2
    if id_string == 'activity_progress_c4d':
        sector_id = 2
    if id_string == 'activity_progress_site_improvement':
        sector_id = 11


    project_query = "with t1 as(SELECT id AS sub_activity_id, activity_id, sub_activity_name, code::text sub_activity_code FROM sub_activity WHERE activity_id =ANY (SELECT id FROM activity WHERE sector_id = "+str(sector_id)+")), t2 AS (SELECT id , activity_name , code::text activity_code FROM activity WHERE sector_id = "+str(sector_id)+"), t3 AS (SELECT * FROM t1 LEFT JOIN t2 ON t1.activity_id = t2.id), t4 AS (SELECT sub_activity_id, (SELECT name FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_name, (select code from project where id = project_id limit 1) project_code, (SELECT id FROM donor WHERE id = (SELECT donor_id FROM project WHERE id = project_id)) donor_code FROM activity_mapping) SELECT  distinct(t4.donor_code||t3.activity_code||t3.sub_activity_code||t4.project_code) project , t4.donor_name||'-'||t4.project_code project_label FROM t3 LEFT JOIN t4 ON t3.sub_activity_id = t4.sub_activity_id where t3.activity_code is not null and t4.donor_code::text like '"+ str(donor) + "' and  t4.donor_code::text||t3.activity_code::text like '"+str(activity)+"' and  t4.donor_code::text||t3.activity_code::text||t3.sub_activity_code::text  like '"+str(sub_activity)+"' and t4.sub_activity_id is not null "
    opt_project_list =  json.dumps(__db_fetch_values_dict(project_query))


    return HttpResponse(opt_project_list)


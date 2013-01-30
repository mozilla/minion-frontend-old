# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.shortcuts import render, redirect
from funfactory.log import log_cef
from django.core.context_processors import csrf
from django.http import HttpResponse, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import simplejson
from django.core import serializers
from mobility.decorators import mobile_template
from session_csrf import anonymous_csrf
from models import Scan
import logging, os, bleach, commonware, urllib2, json, time, requests, urlparse, re

log = commonware.log.getLogger('playdoh')

def _validate_target_url(url):
    """Only accept URLs that are basic. No query, fragment or embedded auth allowed"""
    if not isinstance(url, str) and not isinstance(url, unicode):
        return False
    p = urlparse.urlparse(url)
    if p.scheme not in ('http', 'https'):
        return False
    if p.query or p.fragment or p.username or p.password:
        return False
    return True    

def _validate_plan_name(plan_name, plans):
    """Only accept plans names that are in the given list of plan descriptions."""
    for plan in plans:
        if plan['name'] == plan_name:
            return True

@mobile_template('scanner/home.html')
def home(request, template=None):
    """Home main view"""
    data = {}
    return render(request, template, data)

@mobile_template('scanner/newscan.html')
def newscan(request, template=None):
    """New scan page, form to enter URL, pick a plan, etc."""
    data = {}
    try:
        r = requests.get(settings.TASK_ENGINE_URL + '/plans')
        resp_json = r.json
    except:
        data = {"error":"Error retrieving available plans. Check connection to task engine."}
        #If you can't retrieve the plans, no use in continuing, return error now.
        return render(request, template, data)
    #Page has been POSTed to, create a scan and redirect to /scan/id
    if request.method == 'POST':
        url_entered = request.POST["new_scan_url_input"]
        plan_selected = request.POST["plan_selection"]
        if _validate_target_url(url_entered) and _validate_plan_name(plan_selected, resp_json['plans']):
            #Task Engine work
            #Start the scan using provided url to PUT to the API endpoint
            payload = json.dumps({"target": url_entered})
            try:
                put = requests.put(settings.TASK_ENGINE_URL + "/scan/create/" + plan_selected, data=payload)
                #Decode the response and extract the ID
                put_resp = put.json
                scan_id = put_resp['scan']['id']
                
                #Post START to the API endpoint to begin the scan
                starter = requests.post(settings.TASK_ENGINE_URL + "/scan/" + scan_id + "/state", data="START")
            except:
                data = {"error":"Error starting session. Check connection to the task engine."}
                #If you can't start a session, no use in continuing, return now
                return render(request, template, data)
    
            #Add the new scan to the database
            newscan1 = Scan(scan_id=scan_id, scan_creator=request.user, scan_url=url_entered, scan_plan=plan_selected)
            newscan1.save()
    
            #return render(request, template, data)
            return redirect('/scan/'+scan_id)
        else:
            data = {"error_retry":"Invalid URL or plan. Please enter a valid URL and select a plan.", "plans":resp_json['plans'], "task_engine_url":settings.TASK_ENGINE_URL}
            return render(request, template, data)
    #Page has not been POSTed to
    else:
        data = {"plans":resp_json['plans'], "task_engine_url":settings.TASK_ENGINE_URL}
        return render(request, template, data)
    
@mobile_template('scanner/myscans.html')
def myscans(request, template=None):
    """Page showing all scans by the user"""
    try:
        myscans = Scan.objects.filter(scan_creator=request.user).order_by("-scan_date")
        data = {"scans":myscans}
    except:
        data = {"error":"Database could not be reached. Check database connection."}
    return render(request, template, data)

@mobile_template('scanner/scan.html')
def scan(request, template=None, scan_id="0"):
    try:
        #Retrieve the first set of responses to construct progress bars
        first_results = requests.get(settings.TASK_ENGINE_URL + '/scan/' + scan_id)
        first_results_json = first_results.json
        
        num_high, num_med, num_low, num_info = 0, 0, 0, 0;
        if first_results_json['scan']['state'] in ("FINISHED", "STOPPED"):
            for session in first_results_json['scan']['sessions']:
                for issue in session['issues']:
                    if issue['Severity'] == "High":
                        num_high += 1;
                    elif issue['Severity'] == "Medium":
                        num_med += 1;
                    elif issue['Severity'] == "Low":
                        num_low += 1;
                    elif issue['Severity'] == "Informational" or issue['Severity'] == "Info":
                        num_info += 1;
            
            data = {"finished":"finished","results":first_results_json['scan'],"num_high":num_high,"num_med":num_med,"num_low":num_low, "num_info":num_info}
        else:
            data = {"results":first_results_json['scan'],"num_high":num_high,"num_med":num_med,"num_low":num_low,"num_info":num_info}
        
    except:
        data = {"error":"Error retrieving scan information. Check provided id."}
        return render(request, template, data)

    return render(request, template, data)

@mobile_template('scanner/plans.html')
def plans(request, template=None):
    """Page showing all plans available"""
    try:
        plans = requests.get(settings.TASK_ENGINE_URL + '/plans')
        plans = plans.json
        data = {"plans":plans['plans']}
    except:
        data = {"error":"Error retrieving plans. Check the connection to the task engine."}
    return render(request, template, data)

#
# /xhr_scan_status
#
# This endpoint makes a call to the task-engine to retrieve results
# for a specific scan. It takes two arguments:
#
#  scan_id - the UUID of the scan
#  token - an optional token that will be passed to the task engine
#
# The call is only allowed for logged in users and the user must own
# specified scan.
#
# The call is also has CSRF protection and expects the AJAX client
# to correctly send the CSRF token.
#

def _validate_scan_id(scan_id):
    return scan_id and re.match(r"^([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})$", scan_id)

@csrf_protect
@require_http_methods(["POST"])
def xhr_scan_status(request):

    # Only authenticated users can make this call

    if not request.user.is_authenticated():
        message = {'success': False, 'error': 'unauthorized'}
        return HttpResponse(json.dumps(message), mimetype="application/json")

    # Do some basic checks on the parameters. Specially the scan_id
    # since we use it to build a url to the task engine.

    scan_id = request.POST.get("scan_id")
    scan_token = request.POST.get("token")

    if not _validate_scan_id(scan_id):
        message = {'success': False, 'error': 'invalid-scan-id'}
        return HttpResponse(json.dumps(message), mimetype="application/json")

    # See if the logged in user actually owns the scan

    try:
        scan = Scan.objects.get(scan_creator=request.user,scan_id=scan_id)
    except ObjectDoesNotExist as e:
        message = {'success': False, 'error': 'unknown-scan'}
        return HttpResponse(json.dumps(message), mimetype="application/json")
    except Exception as e:
        logging.exception("Unexpected response from Scan.object.get({},{})".format(request.user.email,scan_id))
        message = {'success': False, 'error': 'internal-error'}
        return HttpResponse(json.dumps(message), mimetype="application/json")

    # Call the task engine and return the results. The task engine
    # will also validate the scan_id and the token and will return
    # a JSON response or non-200 status.

    try:
        params = { 'token': scan_token }
        r = requests.get(settings.TASK_ENGINE_URL + '/scan/' + scan_id + '/results', params=params)
        r.raise_for_status()
        return HttpResponse(r.content)
    except Exception as e:
        logging.exception("Failed to call the task engine")
        message = {'success': False, 'error': 'internal-error'}
        return HttpResponse(json.dumps(message), mimetype="application/json")
        
def download_artifacts(request, scan_id, session_id):

    # Only authenticated users can make this call

    if not request.user.is_authenticated():
        return HttpResponseNotFound()

    # See if the logged in user actually owns the scan

    try:
        scan = Scan.objects.get(scan_creator=request.user,scan_id=scan_id)
    except ObjectDoesNotExist as e:
        return HttpResponseNotFound()
    except Exception as e:
        logging.exception("Unexpected response from Scan.object.get({},{})".format(request.user.email,scan_id))
        return HttpResponseNotFound()

    # See if the user also owns the plugin session. It has to be part of the scan.

    r = requests.get(settings.TASK_ENGINE_URL + '/scan/' + scan_id)
    r.raise_for_status()
    result = r.json
    if not result.get('success'):
        return HttpResponseNotFound()

    scan = r.json['scan']

    session = next((s for s in scan['sessions'] if s['id'] == session_id), None)
    if session is None:
        return HttpResponseNotFound()

    # Grab the artifact from the task engine. This is not ideal. Not sure how to do pass through.
    
    r = requests.get(settings.TASK_ENGINE_URL + '/scan/' + scan_id + '/artifacts/' + session_id)
    if r.status_code != 200:
        return HttpResponseNotFound()

    response = HttpResponse(r.content, content_type="application/zip")
    response['Content-Disposition'] = 'attachment; filename="%s-%s.zip"' % (session['plugin']['name'], session_id[0:8])
    response['Content-Length'] = len(r.content)
    return response

def delete_scan(request):

    # Only authenticated users can make this call

    if not request.user.is_authenticated():
        return redirect('/myscans')

    # See if the logged in user actually owns the scan

    scan_id = request.POST.get("scan_id")
    if not _validate_scan_id(scan_id):
        return redirect('/myscans')

    try:
        scan = Scan.objects.get(scan_creator=request.user,scan_id=scan_id)
        scan.delete()
    except ObjectDoesNotExist as e:
        return redirect('/myscans')
    except Exception as e:
        logging.exception("Unexpected response from Scan.object.get({},{})".format(request.user.email,scan_id))
        return redirect('/myscans')

    r = requests.delete(settings.TASK_ENGINE_URL + '/scan/' + scan_id)

    return redirect('/myscans')
    
def stop_scan(request):

    # Only authenticated users can make this call

    if not request.user.is_authenticated():
        return HttpResponse(json.dumps({'success':False}), mimetype="application/json")

    # See if the logged in user actually owns the scan

    scan_id = request.GET.get("scan_id")
    if not _validate_scan_id(scan_id):
        return HttpResponse(json.dumps({'success':False}), mimetype="application/json")

    try:
        scan = Scan.objects.get(scan_creator=request.user,scan_id=scan_id)
    except ObjectDoesNotExist as e:
        return HttpResponse(json.dumps({'success':False}), mimetype="application/json")
    except Exception as e:
        logging.exception("Unexpected response from Scan.object.get({},{})".format(request.user.email,scan_id))
        return HttpResponse(json.dumps({'success':False}), mimetype="application/json")

    r = requests.post(settings.TASK_ENGINE_URL + '/scan/' + scan_id + "/state", data='STOP')
    r.raise_for_status()
    
    return HttpResponse(json.dumps(r.json), mimetype="application/json")

# Reverse AJAX :-) I find it much easier to render HTML with a Jingo template
# instead of on the JavaScript side.

@mobile_template('scanner/plan_details.html')
def plan_details(request, template=None):

    # Only authenticated users can make this call

    if not request.user.is_authenticated():
        return HttpResponse(json.dumps({'success':False}), mimetype="application/json")

    r = requests.get(settings.TASK_ENGINE_URL + '/plan/' + request.GET['plan_name'])
    r.raise_for_status()
    return render(request, template, r.json)

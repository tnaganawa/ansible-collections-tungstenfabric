#!/usr/bin/python

# Copyright: (c) 2020, Tatsuya Naganawa <tatsuyan201101@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
import json
import requests

vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}

def login_and_check_id(name, obj_type, controller_ip, username, password, state, domain='default-domain', project='default-project', fabric='dummy'):
    config_api_url = 'http://' + controller_ip + ':8082/'
    web_api_url = 'https://' + controller_ip + ':8143/'

    ## check if the fqname exists
    if (obj_type in ['global-system-config']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config"]}' % (obj_type), headers=vnc_api_headers)
    elif (obj_type in ['global-vrouter-config']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "default-global-vrouter-config"]}' % (obj_type), headers=vnc_api_headers)
    elif (obj_type in ['fabric']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "%s"]}' % (obj_type, fabric), headers=vnc_api_headers)
    elif (obj_type in ['virtual-port-group']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "%s", "%s"]}' % (obj_type, fabric, name), headers=vnc_api_headers)
    else:
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["%s", "%s", "%s"]}' % (obj_type, domain, project, name), headers=vnc_api_headers)
    if response.status_code == 200:
      update = True
      uuid = json.loads(response.text).get("uuid")
    else:
      update = False
      uuid=''

    ## login to web API
    web_api = requests.session()
    response = web_api.post(web_api_url + 'authenticate', data=json.dumps({"username": username, "password": password}), headers=vnc_api_headers, verify=False)
    csrftoken=web_api.cookies['_csrf']
    vnc_api_headers["x-csrf-token"]=csrftoken

    js={}
    if update and state=='present':
      response = web_api.post(web_api_url + 'api/tenants/config/get-config-objects', data=json.dumps({"data": [{"type": obj_type, "uuid": ["{}".format(uuid)]}]}), headers=vnc_api_headers, verify=False)
      js = json.loads(response.text)[0]

    return (web_api, update, uuid, js)


##
# crud (web_api, 'present', result, payload)
# crud (web_api, 'absent', result, obj_type='virtual-network', uuid='xxxx-xxxx')
##
def crud(web_api, controller_ip, update, state, result, payload='{}', obj_type='', uuid=''):
    web_api_url = 'https://' + controller_ip + ':8143/'
    failed=False

    csrftoken=web_api.cookies['_csrf']
    vnc_api_headers["x-csrf-token"]=csrftoken

    if state == "present":
      if update:
        print ("update object")
        response = web_api.post(web_api_url + 'api/tenants/config/update-config-object', data=payload, headers=vnc_api_headers, verify=False)
      else:
        print ("create object")
        response = web_api.post(web_api_url + 'api/tenants/config/create-config-object', data=payload, headers=vnc_api_headers, verify=False)
    elif (state == "absent"):
      if update:
        print ("delete object {}".format(uuid))
        response = web_api.post(web_api_url + 'api/tenants/config/delete', data=json.dumps([{"type": obj_type, "deleteIDs": ["{}".format(uuid)]}]), headers=vnc_api_headers, verify=False)
      else:
        result["message"]="delete is requested, but that fq_name is not avaialbe"
        result["changed"]=False
        return True
    message = response.text

    if response.status_code == 200:
      result['changed'] = True
    else:
      result['changed'] = False
      failed = True

    result['message'] = message

    return failed


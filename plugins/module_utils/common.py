#!/usr/bin/python

# Copyright: (c) 2020, Tatsuya Naganawa <tatsuyan201101@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import sys
import os
import json
import requests

# begin: variables: cannot be directly accessed, but can be accessed by get method
vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}
web_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}
config_api_url=""
web_api_url=""
module=None
controller_ip=""
# end: variables


def get_config_api_url():
    return config_api_url

def login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain='default-domain', project='default-project', fabric='dummy', physical_router='dummy'):
    controller_ip = controller_ip
    config_api_url = 'http://' + controller_ip + ':8082/'
    web_api_url = 'https://' + controller_ip + ':8143/'
    module=module

    ##
    # get keystone token
    ##
    if not os.getenv('OS_AUTH_URL') == None:
      os_auth_url = os.getenv('OS_AUTH_URL', 'http://' + controller_ip + ':35357/v3')
      url = os_auth_url + '/auth/tokens?nocatalog'
      os_auth_type = os.getenv('OS_AUTH_TYPE', 'password')
      os_username = os.getenv('OS_USER_NAME', 'admin')
      os_password = os.getenv('OS_PASSWORD', 'contrail123')
      os_project_domain_name = os.getenv('OS_PROJECT_DOMAIN_NAME', 'Default')
      os_user_domain_name = os.getenv('OS_USER_DOMAIN_NAME', 'Default')
      os_project_name = os.getenv('OS_PROJECT_NAME', 'admin')
      keystone_data = {"auth": {"identity": {"methods": ["{}".format(os_auth_type)], "password": {"user": {"name": "{}".format(os_username), "password": "{}".format(os_password), "domain": {"name": "{}".format(os_user_domain_name)}}}}, "scope": {"project": {"name": "{}".format(os_project_name), "domain": {"name": "{}".format(os_project_domain_name)}}}}}
      response = requests.post(url, data=json.dumps(keystone_data), headers=vnc_api_headers)
      if not (response.status_code == 200 or response.status_code == 201):
        module.fail_json("keystone token cannot be obtained")

      keystone_token = response.headers.get("X-Subject-Token")
      vnc_api_headers["x-auth-token"]=keystone_token

    ## check if the fqname exists
    if (obj_type in ['global-system-config']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config"]}' % (obj_type), headers=vnc_api_headers)
    elif (obj_type in ['virtual-machine'] or (obj_type == 'tag' and project == None)):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["%s"]}' % (obj_type, name), headers=vnc_api_headers)
    elif (obj_type in ['global-vrouter-config']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "default-global-vrouter-config"]}' % (obj_type), headers=vnc_api_headers)
    elif (obj_type in ['bgp-router']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-domain", "default-project", "ip-fabric", "__default__", "%s"]}' % (obj_type, name), headers=vnc_api_headers)
    elif (obj_type in ['fabric', 'api-access-list']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "%s"]}' % (obj_type, name), headers=vnc_api_headers)
    elif (obj_type in ['virtual-port-group']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "%s", "%s"]}' % (obj_type, fabric, name), headers=vnc_api_headers)
    elif (obj_type in ['physical-interface']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["default-global-system-config", "%s", "%s"]}' % (obj_type, physical_router, name), headers=vnc_api_headers)
    elif (obj_type in ['service-template']):
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["%s", "%s"]}' % (obj_type, domain, name), headers=vnc_api_headers)
    else:
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "%s", "fq_name": ["%s", "%s", "%s"]}' % (obj_type, domain, project, name), headers=vnc_api_headers)
    if response.status_code == 200:
      update = True
      uuid = json.loads(response.text).get("uuid")
    elif response.status_code == 404:
      update = False
      uuid=''
    elif response.status_code == 401:
      module.fail_json("config-api's /fqname-to-id access is not authorized. please check keystone client env, such as OS_AUTH_URL.")
    else:
      module.fail_json("config-api's /fqname-to-id failed.")

    ## login to web API
    web_api = requests.session()
    response = web_api.post(web_api_url + 'authenticate', data=json.dumps({"username": username, "password": password}), headers=web_api_headers, verify=False)
    csrftoken=web_api.cookies['_csrf']
    web_api_headers["x-csrf-token"]=csrftoken

    js={}
    if update and (state=='present' or obj_type == 'api-access-list'):
      response = web_api.post(web_api_url + 'api/tenants/config/get-config-objects', data=json.dumps({"data": [{"type": obj_type, "uuid": ["{}".format(uuid)]}]}), headers=web_api_headers, verify=False)
      js = json.loads(response.text)[0]

    return (web_api, update, uuid, js)


##
# crud (web_api, 'present', result, payload)
# crud (web_api, 'absent', result, obj_type='virtual-network', uuid='xxxx-xxxx')
##
def crud(web_api, controller_ip, update, state, result, payload='{}', obj_type='', uuid='', userData={}):
    web_api_url = 'https://' + controller_ip + ':8143/'
    failed=False

    csrftoken=web_api.cookies['_csrf']
    vnc_api_headers["x-csrf-token"]=csrftoken

    if state == "present" or obj_type == 'api-access-list':
      if update:
        print ("update object")

        if obj_type == 'service-instance':
          response = web_api.put(web_api_url + 'api/tenants/config/service-instances/' + uuid, data=payload, headers=web_api_headers, verify=False)
        else:
          response = web_api.post(web_api_url + 'api/tenants/config/update-config-object', data=payload, headers=web_api_headers, verify=False)
      else:
        print ("create object")
        if obj_type == 'service-instance':
          response = web_api.post(web_api_url + 'api/tenants/config/service-instances', data=payload, headers=web_api_headers, verify=False)
        elif obj_type == 'loadbalancer':
          response = web_api.post(web_api_url + 'api/tenants/config/lbaas/load-balancer', data=payload, headers=web_api_headers, verify=False)
        else:
          response = web_api.post(web_api_url + 'api/tenants/config/create-config-object', data=payload, headers=web_api_headers, verify=False)
    elif (state == "absent"):
      if update:
        print ("delete object {}".format(uuid))
        if obj_type == 'loadbalancer':
          response = web_api.post(web_api_url + 'api/tenants/config/lbaas/load-balancer/delete', data=json.dumps({"uuids": [uuid]}), headers=web_api_headers, verify=False)
        else:
          delete_data=[{"type": obj_type, "deleteIDs": ["{}".format(uuid)]}]
          if not userData == {}:
            delete_data[0]["userData"]=userData
          response = web_api.post(web_api_url + 'api/tenants/config/delete', data=json.dumps(delete_data), headers=web_api_headers, verify=False)
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


def fqname_to_id (module, fqname, obj_type, controller_ip):
  config_api_url = 'http://' + controller_ip + ':8082/'
  if (type(fqname) == str):
    fqname_list = fqname.split (":")
  else:
    fqname_list = fqname

  response = requests.post(config_api_url + 'fqname-to-id', data=json.dumps({"type": obj_type, "fq_name": fqname_list}), headers=vnc_api_headers)
  if not response.status_code == 200:
    module.fail_json(msg="{} specified doesn't exist".fqname, **result)
  uuid = json.loads(response.text).get("uuid")
  return uuid

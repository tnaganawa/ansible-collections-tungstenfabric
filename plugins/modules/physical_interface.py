#!/usr/bin/python

# Copyright: (c) 2020, Tatsuya Naganawa <tatsuyan201101@gmail.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}

DOCUMENTATION = '''
---
module: physical_interface

short_description: create tungstenfabirc physical-interface

version_added: "2.9"

description:
    - "create / delete tungstenfabric physical-interface"

options:
    name:
        description:
            - physical-interface name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    physical-router:
        description:
            - physical-router for this physical-interface
        required: true
    share:
        description:
            - share this physical-interface to specified tenant with specified permission
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create physical-interface
  tungstenfabric.networking.physical_interface:
    name: xe-0/1/0
    controller_ip: x.x.x.x
    state: present
    physical_router: leaf1
    share: [[tenant1, 5]]

- name: delete physical-interface
  tungstenfabric.networking.physical_interface:
    name: xe-0/1/0
    controller_ip: x.x.x.x
    state: absent
    physical_router: leaf1

'''

RETURN = '''
message:
    description: The output message that this module generates
    type: str
    returned: always
'''



import sys
import json
import requests
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.tungstenfabric.networking.plugins.module_utils.common import login_and_check_id, crud, vnc_api_headers

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='admin'),
        physical_router=dict(type='str', required=True),
        share=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name = module.params.get("name")
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    physical_router = module.params.get("physical_router")
    share = module.params.get("share")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='physical-interface'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project, phyical_router=physical_router)

    ## begin: object specific
    config_api_url = 'http://' + controller_ip + ':8082/'

    failed=False


    ## create physical_interface_refs when physical_interface is not empty
    physical_interface_refs=[]
    if state == 'present' and physical_interfaces:
      pass

    if update:
      if state == 'present':

        if not share == None:
          tmp_share_list=[]
          for tenant_name, tenant_permission in share:
            response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "project", "fq_name": ["%s", "%s"]}' % (domain, tenant_name), headers=vnc_api_headers)
            if not response.status_code == 200:
              failed = True
              result["message"] = response.text
              module.fail_json(msg="uuid of specified shared project cannot be obtained", **result)
            project_uuid = json.loads(response.text).get("uuid")
            tmp_share_list.append({"tenant": project_uuid, "tenant_access": tenant_permission})
          js["physical-interface"]["perms2"]["share"]=tmp_share_list


        response = requests.put(config_api_url + 'physical-interface/' + uuid, data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="physical-interface update failed", **result)

      elif state == 'absent':
        # delete physical-interface
        response = requests.delete(config_api_url + 'physical-interface/' + uuid, data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="physical-interface deletion failed", **result)
    else:
      if state == 'present':
        js=json.loads (
        '''
        { "physical-interface":
          {
            "fq_name": ["default-global-system-config", "%s", "%s"],
            "parent_type": "physical-router"
          }
        }
        ''' % (physical_router, name)
        )
        response = requests.post(config_api_url + 'physical-interfaces', data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="physical-interface creation failed", **result)

      else:
        module.fail_json(msg="physical-interface doesn't exist", **result)


    ## end: object specific


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

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
module: logical_router

short_description: create tungstenfabirc logical-router

version_added: "2.10"

description:
    - "create / delete tungstenfabric logical-router"

options:
    name:
        description:
            - logical-router name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - logical-router domain
        required: false
    project:
        description:
            - logical-router project
        required: false
    router_type:
        description:
            - logical-router type (snat-routing / vxlan-routing)
        required: false
    connected_networks:
        description:
            - virtual-networks connected to this logical-router
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create logical-router
  tungstenfabric_logical_router:
    name: lr1
    controller_ip: x.x.x.x
    state: present
    project: admin
    router_type: vxlan-routing
    connected_networks: [vn1, vn2]

- name: delete logical-router
  tungstenfabric_logical_router:
    name: lr1
    controller_ip: x.x.x.x
    state: absent
    project: admin

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
import ansible_collections.tungstenfabric.networking.plugins.module_utils.common

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        uuid=dict(type='str', required=False),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='default-project'),
        router_type=dict(type='str', required=False, choices=['snat-routing', 'vxlan-routing']),
        connected_networks=dict(type='list', required=False)
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
    router_type = module.params.get("router_type")
    connected_networks = module.params.get("connected_networks")

    if module.check_mode:
        module.exit_json(**result)

    ## begin: logical-router
    obj_type='logical-router'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    ## create payload and call API
    if update and state=='present':
      pass
    else:
      js=json.loads (
      '''
      { "logical-router":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
      )

    if router_type:
      js ["logical-router"]["logical_router_type"]=router_type

    print ("connected_networks", connected_networks)
    if len(connected_networks) > 0:
      print ("try to connect", connected_networks)
      js ["logical-router"]["virtual_machine_interface_refs"]=[]
      for network in connected_networks:
        js ["logical-router"]["virtual_machine_interface_refs"].append(
         {
           "parent_type":"project",
           "fq_name": [domain,project],
           "virtual_network_refs":[{"to":[domain, project, network]}],
           "virtual_machine_interface_device_owner":"network:router_interface"
         }
        )


    if state == "present":
      if update:
        print ("update object")
        js["logical-router"]["uuid"]=uuid
        response = client.post(web_api_url + 'api/tenants/config/update-config-object', data=json.dumps(js), headers=vnc_api_headers, verify=False)
      else:
        print ("create object")
        response = client.post(web_api_url + 'api/tenants/config/create-config-object', data=json.dumps(js), headers=vnc_api_headers, verify=False)
    elif (state == "absent"):
      if update:
        print ("delete object {}".format(uuid))
        response = client.post(web_api_url + 'api/tenants/config/delete', data=json.dumps([{"type": "logical-router", "deleteIDs": ["{}".format(uuid)]}]), headers=vnc_api_headers, verify=False)
      else:
        failed = True
    message = response.text

    if response.status_code == 200:
      result['changed'] = True
    else:
      result['changed'] = False
      failed = True

    result['message'] = message

    ## end: logical-router

    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

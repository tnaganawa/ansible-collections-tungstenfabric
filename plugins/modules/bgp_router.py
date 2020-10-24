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
module: bgp_router

short_description: create tungstenfabirc bgp-router

version_added: "2.9"

description:
    - "create / delete tungstenfabric bgp-router"

options:
    name:
        description:
            - bgp-router name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - bgp-router subnet
        required: false
    project:
        description:
            - bgp-router subnet
        required: false
    policy_rule:
        description:
            - rule of this bgp-router (see EXAMPLES)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create bgp-router
  tungstenfabric.networking.bgp_router:
    name: bgp-router1
    controller_ip: x.x.x.x
    state: present
    address: 192.168.122.101
    autonomous_system: 64512
    bgp_router_refs: [controller1]

- name: delete bgp-router
  tungstenfabric.bgp_router.bgp_router:
    name: bgp-router1
    controller_ip: x.x.x.x
    state: absent
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
from ansible_collections.tungstenfabric.networking.plugins.module_utils.common import login_and_check_id, crud

def run_module():
    module_args = dict(
        name=dict(type='str', required=True),
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        uuid=dict(type='str', required=False),
        address=dict(type='str', required=True),
        vendor=dict(type='str', required=False, default=''),
        router_type=dict(type='str', required=False, default='router', choices=['control-node', 'external-control-node', 'router']),
        hold_time=dict(type='int', required=False, default=90),
        admin_down=dict(type='bool', required=False, default=False),
        address_families=dict(type='list', required=False),
        autonomous_system=dict(type='int', required=True),
        bgp_router_refs=dict(type='list', required=False)
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
    router_type = module.params.get("router_type")
    address = module.params.get("address")
    vendor = module.params.get("vendor")
    hold_time = module.params.get("hold_time")
    admin_down = module.params.get("admin_down")
    address_families = module.params.get("address_families")
    autonomous_system = module.params.get("autonomous_system")
    bgp_router_refs = module.params.get("bgp_router_refs")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='bgp-router'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "bgp-router":
        {
          "fq_name": ["default-domain","default-project","ip-fabric","__default__", "%s"],
          "parent_type": "routing-instance"
        }
      }
      ''' % (name)
    )

    ## begin: object specific
    if js["bgp-router"].get("bgp_router_parameters") == None:
      bgp_router_parameters={}
      js["bgp-router"]["bgp_router_parameters"]=bgp_router_parameters
    else:
      bgp_router_parameters = js["bgp-router"]["bgp_router_parameters"]

    if router_type:
      bgp_router_parameters["router_type"] = router_type
    if address:
      bgp_router_parameters["address"] = address
      bgp_router_parameters["identifier"] = address
    if vendor:
      bgp_router_parameters["vendor"] = vendor
    if hold_time:
      bgp_router_parameters["hold_time"] = hold_time
    if admin_down:
      bgp_router_parameters["admin_down"] = admin_down
    if autonomous_system:
      bgp_router_parameters["autonomous_system"] = autonomous_system
    if address_families:
      bgp_router_parameters["address_families"] = address_families

    if bgp_router_refs:
      js["bgp-router"]["bgp_router_refs"] = [{"to": ["default-domain", "default-project", "ip-fabric", "__default__", bgp_router], "attr": None} for bgp_router in bgp_router_refs]

    ## end: object specific


    payload=json.dumps(js)

    failed = crud (web_api, controller_ip, update, state, result, payload=payload, obj_type=obj_type, uuid=uuid)


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

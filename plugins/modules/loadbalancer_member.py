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
module: loadbalancer_member

short_description: create tungstenfabirc loadbalancer-member

version_added: "2.9"

description:
    - "create / delete tungstenfabric loadbalancer-member"

options:
    name:
        description:
            - loadbalancer-member name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - loadbalancer-member subnet
        required: false
    project:
        description:
            - loadbalancer-member subnet
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create loadbalancer-member
  tungstenfabric.networking.loadbalancer_member:
    name: loadbalancer-member1
    controller_ip: x.x.x.x
    state: present
    project: admin
    loadbalancer_subnet_uuid: xxxx-xxxx-xxxx-xxxx
    loadbalancer_pool_uuid: xxxx-xxxx-xxxx-xxxx
    address: 10.0.11.13
    port: 80

- name: delete loadbalancer-member
  tungstenfabric.networking.loadbalancer_member:
    name: loadbalancer-member1
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
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='default-project'),
        loadbalancer_subnet_uuid=dict(type='str', required=False),
        loadbalancer_pool_uuid=dict(type='str', required=False),
        address=dict(type='str', required=False),
        port=dict(type='int', required=False),
        weight=dict(type='int', required=False, default=1)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["state", "present", ["loadbalancer_subnet_uuid", "loadbalancer_pool_uuid", "address", "port"]]
    ]

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=required_if_args
    )

    name = module.params.get("name")
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    loadbalancer_subnet_uuid = module.params.get("loadbalancer_subnet_uuid")
    loadbalancer_pool_uuid = module.params.get("loadbalancer_pool_uuid")
    address = module.params.get("address")
    port = module.params.get("port")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='loadbalancer-member'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project, loadbalancer_pool=loadbalancer_pool_uuid)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "loadbalancer-member":
        {
          "fq_name": ["%s", "%s", "%s", "%s"],
          "parent_type": "loadbalancer-pool"
        }
      }
      ''' % (domain, project, loadbalancer_pool_uuid, name)
    )

    ## begin: object specific
    if (address):
      js["loadbalancer-member"]["loadbalancer_member_properties"]["subnet_id"] =  loadbalancer_pool_uuid
    if (address):
      js["loadbalancer-member"]["loadbalancer_member_properties"]["address"] =  address
    if (port):
      js["loadbalancer-member"]["loadbalancer_member_properties"]["protocol_port"] = port
    if (weight):
      js["loadbalancer-member"]["loadbalancer_member_properties"]["weight"] = weight
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

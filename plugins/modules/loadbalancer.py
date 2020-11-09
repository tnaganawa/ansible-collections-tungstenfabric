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
module: loadbalancer

short_description: create tungstenfabirc loadbalancer

version_added: "2.9"

description:
    - "create / delete tungstenfabric loadbalancer"

options:
    name:
        description:
            - loadbalancer name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - loadbalancer subnet
        required: false
    project:
        description:
            - loadbalancer subnet
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create loadbalancer
  tungstenfabric.networking.loadbalancer:
    name: loadbalancer1
    controller_ip: x.x.x.x
    state: present
    project: admin
    loadbalancer_subnet_uuid: xxxx-xxxx-xxxx-xxxx
    loadbalancer_member_address_list: [10.0.11.11, 10.0.11.12]
    loadbalancer_member_port_list: [80, 80]

- name: delete loadbalancer
  tungstenfabric.networking.loadbalancer:
    name: loadbalancer1
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
        loadbalancer_provider=dict(type='str', required=False, default='opencontrail', choices=['native', 'opencontrail']),
        loadbalancer_member_address_list=dict(type='list', required=False),
        loadbalancer_member_port_list=dict(type='list', required=False)
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
    policy_rule = module.params.get("policy_rule")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='loadbalancer'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      {
        { "loadbalancer":
          {
            "fq_name": ["%s", "%s", "%s"],
            "loadbalancer_properties": {
              "vip_subnet_id": %s
            },
            "parent_type": "project"
          }
        },
        { "loadbalancer-healthmonitor":
          {
            "fq_name": ["%s", "%s", "%s-healthmonitor"],
            "parent_type": "project"
          }
        },
        { "loadbalancer-listener":
          {
            "fq_name": ["%s", "%s", "%s-listener"],
            "parent_type": "project"
          }
        },
        { "loadbalancer-pool":
          {
            "fq_name": ["%s", "%s", "%s-pool"],
            "parent_type": "project"
          }
        }
      }
      ''' % (domain, project, name, loadbalancer_subnet_uuid, domain, project, name, domain, project, name)
    )

    ## begin: object specific
    js["loadbalancer"]["loadbalancer_provider"] = loadbalancer_provider

    if not update:
      js["loadbalancer-member"] = []
      for i in range(len(loadbalancer_member_address_list):
        js["loadbalancer-member"].append(
          {
            "fq_name": [domain, project, "{}-member-{}".format(name, i)],
            "parent_type": "loadbalancer-pool",
            "loadbalancer_member_properties": {
              "address": loadbalancer_member_address_list[i],
              "loadbalancer_member_properties": loadbalancer_member_port_list[i]
            }
          }
        )

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

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
module: network_policy

short_description: create tungstenfabirc network-policy

version_added: "2.9"

description:
    - "create / delete tungstenfabric network-policy"

options:
    name:
        description:
            - network-policy name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - network-policy subnet
        required: false
    project:
        description:
            - network-policy subnet
        required: false
    policy_rule:
        description:
            - rule of this network-policy (see EXAMPLES)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create network-policy
  tungstenfabric.networking.network_policy:
    name: network-policy1
    controller_ip: x.x.x.x
    state: present
    project: admin
    policy_rule:
      - src_addresses:
          - virtual_network: default-domain:admin:vn1
        dst_addresses:
          - virtual_network: default-domain:admin:vn2
        protocol: any
        action_list:
          simple_action: pass

- name: delete network-policy
  tungstenfabric.network_policy.network_policy:
    name: network-policy1
    controller_ip: x.x.x.x
    state: absent

- name: create network-policy with network service
  tungstenfabric.network.network_policy:
    name: network-policy1
    controller_ip: x.x.x.x
    state: present
    project: admin
    policy_rule:
      - src_addresses:
          - virtual_network: default-domain:admin:vn1
        dst_addresses:
          - virtual_network: default-domain:admin:vn2
        protocol: any
        action_list:
          simple_action: pass
          apply_service:
            - default-domain:admin:vn1-to-vn2
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
        policy_rule=dict(type='list', required=False)
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

    obj_type='network-policy'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "network-policy":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
    )

    ## begin: object specific
    if (policy_rule):
      tmp_policy_rule = policy_rule[:]

      for i in range(len(tmp_policy_rule)):
        # set default values for policy rules
        if tmp_policy_rule[i].get("direction") == None:
          tmp_policy_rule[i]["direction"]="<>"
        if tmp_policy_rule[i].get("src_ports") == None:
          tmp_policy_rule[i]["src_ports"]=[{"start_port": -1, "end_port": -1}]
        if tmp_policy_rule[i].get("dst_ports") == None:
          tmp_policy_rule[i]["dst_ports"]=[{"start_port": -1, "end_port": -1}]

      js["network-policy"]["network_policy_entries"] = {"policy_rule": tmp_policy_rule}

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

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
module: firewall_rule

short_description: create tungstenfabirc firewall-rule

version_added: "2.9"

description:
    - "create / delete tungstenfabric firewall-rule"

options:
    name:
        description:
            - firewall-rule name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    project:
        description:
            - project name (if it is defined, firewall-rule will be project scoped rule)
        required: false
    firewall_rule:
        description:
            - rule of this firewall-rule (see EXAMPLES)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create firewall_rule
  tungstenfabric.networking.firewall_rule:
    name: firewall_rule1
    controller_ip: x.x.x.x
    state: present
    endpoint_1: {virtual_network: default-domain:admin:vn1}
    endpoint_2: {virtual_network: default-domain:admin:vn2}
    service: {protocol: any}
    action_list: {simple_action: pass}

- name: create project-scope firewall_rule
  tungstenfabric.networking.firewall_rule:
    name: firewall_rule1
    controller_ip: x.x.x.x
    state: present
    project: admin
    endpoint_1: {virtual_network: default-domain:admin:vn1}
    endpoint_2: {virtual_network: default-domain:admin:vn2}
    service: {protocol: any}
    action_list: {simple_action: pass}

- name: delete firewall_rule
  tungstenfabric.networking.firewall_rule:
    name: firewall_rule1
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
        project=dict(type='str', required=False),
        endpoint_1=dict(type='dict', required=False),
        endpoint_2=dict(type='dict', required=False),
        service=dict(type='dict', required=False),
        action_list=dict(type='dict', required=False),
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["state", "present", ["endpoint_1", "endpoint_2", "action_list"]]
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
    endpoint_1 = module.params.get("endpoint_1")
    endpoint_2 = module.params.get("endpoint_2")
    service = module.params.get("service")
    action_list = module.params.get("action_list")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='firewall-rule'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      if project:
        js=json.loads (
        '''
        { "firewall-rule":
          {
            "fq_name": ["%s", "%s", "%s"],
            "parent_type": "project"
          }
        }
        ''' % (domain, project, name)
      )
      else:
        js=json.loads (
        '''
        { "firewall-rule":
          {
            "fq_name": ["%s"],
            "parent_type": "policy-management"
          }
        }
        ''' % (name)
      )

    ## begin: object specific
    if (endpoint_1):
      js["firewall-rule"]["endpoint_1"]=endpoint_1
    if (endpoint_2):
      js["firewall-rule"]["endpoint_2"]=endpoint_2
    if (action_list):
      js["firewall-rule"]["action_list"]=action_list

    # set default values for webui
    if js["firewall-rule"]["endpoint_1"].get("address_group") == None:
      js["firewall-rule"]["endpoint_1"]["address_group"] = None
    if js["firewall-rule"]["endpoint_1"].get("any") == None:
      js["firewall-rule"]["endpoint_1"]["any"] = None
    if js["firewall-rule"]["endpoint_1"].get("tags") == None:
      js["firewall-rule"]["endpoint_1"]["tags"] = []
    if js["firewall-rule"]["endpoint_2"].get("address_group") == None:
      js["firewall-rule"]["endpoint_2"]["address_group"] = None
    if js["firewall-rule"]["endpoint_2"].get("any") == None:
      js["firewall-rule"]["endpoint_2"]["any"] = None
    if js["firewall-rule"]["endpoint_2"].get("tags") == None:
      js["firewall-rule"]["endpoint_2"]["tags"] = []


    if js["firewall-rule"].get("direction") == None:
      js["firewall-rule"]["direction"]="<>"
    if js["firewall-rule"].get("match_tag_types") == None:
      js["firewall-rule"]["match_tag_types"]= {"tag_type": []}

    if (service):
      js["firewall-rule"]["service"] = service

    if js["firewall-rule"].get("service") == None:
      js["firewall-rule"]["service"] = {}

    if js["firewall-rule"]["service"].get("protocol") == None:
      js["firewall-rule"]["service"]["protocol"]="any"
    if js["firewall-rule"]["service"].get("src_ports") == None:
      js["firewall-rule"]["service"]["src_ports"]={"start_port": 0, "end_port": 65535}
    if js["firewall-rule"]["service"].get("dst_ports") == None:
      js["firewall-rule"]["service"]["dst_ports"]={"start_port": 0, "end_port": 65535}
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

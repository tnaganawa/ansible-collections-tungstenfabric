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
module: firewall_policy

short_description: create tungstenfabirc firewall-policy

version_added: "2.9"

description:
    - "create / delete tungstenfabric firewall-policy"

options:
    name:
        description:
            - firewall-policy name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    project:
        description:
            - project name (if it is defined, firewall-policy will be project scoped rule)
        required: false
    firewall_policy:
        description:
            - rule of this firewall-policy (see EXAMPLES)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create firewall_policy
  tungstenfabric.networking.firewall_policy:
    name: firewall-policy1
    controller_ip: x.x.x.x
    state: present
    firewall_rules: [firewall-rule1]

- name: create project-scope firewall_policy
  tungstenfabric.networking.firewall_policy:
    name: firewall-policy1
    controller_ip: x.x.x.x
    state: present
    project: admin
    firewall_rules: [firewall-rule1]

- name: delete firewall_policy
  tungstenfabric.networking.firewall_policy:
    name: firewall-policy1
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
from ansible_collections.tungstenfabric.networking.plugins.module_utils.common import login_and_check_id, crud, vnc_api_headers

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
        firewall_rules=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["state", "present", ["firewall_rules"]]
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
    firewall_rules = module.params.get("firewall_rules")

    if module.check_mode:
        module.exit_json(**result)


    config_api_url = 'http://' + controller_ip + ':8082/'

    obj_type='firewall-policy'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      if project:
        js=json.loads (
        '''
        { "firewall-policy":
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
        { "firewall-policy":
          {
            "fq_name": ["%s"],
            "parent_type": "policy-management"
          }
        }
        ''' % (name)
      )

    ## begin: object specific
    if (firewall_rules):
      firewall_rule_refs = []
      for i in range(len(firewall_rules)):
        # get uuid of each firewall rule
        firewall_rule_name = firewall_rules[i]
        if project:
          firewall_rule_fqname = [domain, project, firewall_rule_name]
        else:
          firewall_rule_fqname = ["default-policy-management", firewall_rule_name]
        response = requests.post(config_api_url + 'fqname-to-id', data=json.dumps({"type": "firewall-rule", "fq_name": firewall_rule_fqname}), headers=vnc_api_headers)
        if not response.status_code == 200:
          module.fail_json(msg="specified firewall-rule doesn't exist", **result)
        firewall_rule_uuid = json.loads(response.text).get("uuid")
        firewall_rule_refs.append({"attr": {"sequence": "{}".format(i)}, "to": firewall_rule_fqname, "uuid": firewall_rule_uuid})
      js["firewall-policy"]["firewall_rule_refs"] = firewall_rule_refs
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

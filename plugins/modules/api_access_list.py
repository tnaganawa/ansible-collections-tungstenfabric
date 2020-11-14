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
module: tag

short_description: create tungstenfabirc tag

version_added: "2.9"

description:
    - "create / delete tungstenfabric tag"

options:
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create a rule in api-access-list
  tungstenfabric.networking.api_access_list:
    controller_ip: x.x.x.x
    state: present
    rule_object: virtual-network
    rule_field: "*"
    role_crud_list: ["CRUD"]
    role_name_list: ["_member_"]

- name: delete a rule from api-access-list
  tungstenfabric.networking.api_access_list:
    controller_ip: x.x.x.x
    state: absent
    rule_object: virtual-network
    rule_field: "*"

- name: add rbac rule similar to horizon
  hosts: localhost
  gather_facts: false
  tasks:
  - name: add rbac rule similar to horizon
    tungstenfabric.networking.api_access_list:
      controller_ip: x.x.x.x
      state: present
      rule_object: "{{ item[0] }}"
      rule_field: "{{ item[1] }}"
      role_crud_list: "{{ item[2] }}"
      role_name_list: "{{ item[3] }}"

    loop:
      ## for openstack objects
      - [virtual-network, "*", ["CRUD"], ["_member_"]]
      - [logical-router, "*", ["CRUD"], ["_member_"]]
      - [network-ipam, "*", ["R"], ["_member_"]]
      - [network-policy, "*", ["R"], ["_member_"]]
      - [security-group, "*", ["CRUD"], ["_member_"]]
      - [virtual-machine-interface, "*", ["R"], ["_member_"]]
      - [routing-policy, "*", ["R"], ["_member_"]]
      ## for fabric objects
      - [virtual-port-group, "*", ["CRUD"], ["_member_"]]
      - [project, "*", ["R"], ["_member_"]]
      - [fabric, "*", ["R"], ["_member_"]] ## visible only when it is shared to that tenant
      - [physical-router, "*", ["R"], ["_member_"]] ## visible only when it is shared to that tenant
      - [physical-interface, "*", ["R"], ["_member_"]] ## visible only when it is shared to that tenant
      - [port-profile, "*", ["R"], ["_member_"]]
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
        name=dict(type='str', required=False),
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        uuid=dict(type='str', required=False),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False),
        rule_object=dict(type='str', required=True),
        rule_field=dict(type='str', required=True),
        role_crud_list=dict(type='list', required=False),
        role_name_list=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["state", "present", ["role_crud_list", "role_name_list"]]
    ]

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=required_if_args
    )

    name = "default-api-access-list"
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    rule_object = module.params.get("rule_object")
    rule_field = module.params.get("rule_field")
    role_crud_list = module.params.get("role_crud_list")
    role_name_list = module.params.get("role_name_list")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='api-access-list'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update:
      pass
    else:
      module.fail_json(msg='default-api-access-list is not available. cannot add an entry to that.', **result)

    ## begin: object specific
    rbac_rule = js["api-access-list"].get("api_access_list_entries").get("rbac_rule")

    entry_to_be_deleted = -1
    for i in range(len(rbac_rule)):
      rbac_entry = rbac_rule[i]
      tmp_rule_object = rbac_entry.get("rule_object")
      tmp_rule_field = rbac_entry.get("rule_field")
      if tmp_rule_object == rule_object and tmp_rule_field == rule_field:
        if state == 'present':
          module.fail_json(msg='That entry is already available. please firstly delete and re-create it.', **result)
        if state == 'absent':
          entry_to_be_deleted = i

    if state == 'present':
      rule_perms = []
      for i in range(len(role_name_list)):
        rule_perms.append({"role_name": role_name_list[i], "role_crud": role_crud_list[i]})
      rbac_rule.append ({"rule_object": rule_object, "rule_field": rule_field, "rule_perms": rule_perms})
    elif state == 'absent':
      if entry_to_be_deleted == -1:
        module.fail_json(msg='cannot find rbac entry that matches the given rule.', **result)
      del rbac_rule[entry_to_be_deleted]
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

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
    name:
        description:
            - tag name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    project:
        description:
            - project name (if it is defined, tag will be project scoped tag)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create tag
  tungstenfabric.networking.tag:
    name: tag1
    controller_ip: x.x.x.x
    state: present
    project: admin
    tag_type: label

- name: delete tag
  tungstenfabric.networking.tag:
    name: tag1
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
        tag_type=dict(type='str', required=False, default='label', choices=["application", "site", "deployment", "tier", "label"])
    )
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    required_if_args = [
      ["state", "present", ["tag_type"]]
    ]

    name = module.params.get("name")
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    tag_type = module.params.get("tag_type")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='tag'
    tag_type_name = tag_type + '=' + name

    (web_api, update, uuid, js) = login_and_check_id(module, tag_type_name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      if project:
        js=json.loads (
        '''
        { "tag":
          {
            "fq_name": ["%s", "%s", "%s"],
            "tag_type_name": "%s",
            "tag_value": "%s",
            "parent_type": "project"
          }
        }
        ''' % (domain, project, name, tag_type, name)
      )
      else:
        js=json.loads (
        '''
        { "tag":
          {
            "fq_name": ["%s"],
            "tag_type_name": "%s",
            "tag_value": "%s"
          }
        }
        ''' % (name, tag_type, name)
      )

    ## begin: object specific
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

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
module: service_instance

short_description: create tungstenfabirc service-instance

version_added: "2.9"

description:
    - "create / delete tungstenfabric service-instance"

options:
    name:
        description:
            - service-instance name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - service-instance domain
        required: false
    project:
        description:
            - service-instance project
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create service-instance
  tungstenfabric.service_instance.service_instance:
    name: service-instance1
    controller_ip: x.x.x.x
    state: present

- name: delete service-instance
  tungstenfabric.service_instance.service_instance:
    name: service-instance1
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
        mgmt_virtual_network=dict(type='str', required=False),
        left_virtual_network=dict(type='str', required=True),
        right_virtual_network=dict(type='str', required=True),
        service_template=dict(type='str', required=True)
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
    mgmt_virtual_network = module.params.get("mgmt_virtual_network")
    left_virtual_network = module.params.get("left_virtual_network")
    right_virtual_network = module.params.get("right_virtual_network")
    service_template = module.params.get("service_template")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='service-instance'

    (web_api, update, uuid, js) = login_and_check_id(name, obj_type, controller_ip, username, password, state, domain=domain, project=project)


    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "service-instance":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
    )

    ## begin: object specific
    js["service-instance"]["service_instance_properties"] = {"interface_list": [{"virtual_network": left_virtual_network}, {"virtual_network": right_virtual_network}], "left_virtual_network": left_virtual_network, "right_virtual_network": right_virtual_network, "service_template_refs": [{"to": [domain, service_template]}]}
    if mgmt_virtual_network:
      js["service-instance"]["service_instance_properties"]["interface_list"].append({"virtual_network": mgmt_virtual_network})

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

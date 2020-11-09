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
module: service_template

short_description: create tungstenfabirc service-template

version_added: "2.9"

description:
    - "create / delete tungstenfabric service-template"

options:
    name:
        description:
            - service-template name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - service-template subnet
        required: false
    service_mode:
        description:
            - service mode (transparent, in-network, in-network-nat)
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create service-template
  tungstenfabric.networking.service_template:
    name: l3
    controller_ip: x.x.x.x
    state: present
    service_mode: in-network

- name: delete service-template
  tungstenfabric.networking.service_template:
    name: l3
    controller_ip: x.x.x.x
    state: absent
    service_mode: in-network

- name: create service-template with some more parameters
  tungstenfabric.networking.service_template:
    name: l3
    controller_ip: x.x.x.x
    state: present
    service_mode: in-network
    interface_type_list: [management, left, right]
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
        service_virtualization_type=dict(type='str', required=False, default='virtual-machine'),
        service_mode=dict(type='str', required=True, choices=['transparent', 'in-network', 'in-network-nat']),
        service_type=dict(type='str', required=False, default='firewall'),
        version=dict(type='int', required=False, default='2'),
        interface_type_list=dict(type='list', required=False, default=['left', 'right'])
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
    service_virtualization_type = module.params.get("service_virtualization_type")
    service_mode = module.params.get("service_mode")
    service_type = module.params.get("service_type")
    version = module.params.get("version")
    interface_type_list = module.params.get("interface_type_list")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='service-template'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project='dummy')


    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "service-template":
        {
          "fq_name": ["%s", "%s"],
          "parent_type": "domain"
        }
      }
      ''' % (domain, name)
    )

    ## begin: object specific
    if (js["service-template"].get("service_template_properties") == None):
      js["service-template"]["service_template_properties"] = {}
    if (service_virtualization_type):
      js["service-template"]["service_template_properties"]["service_virtualization_type"] = service_virtualization_type
    if (service_mode):
      js["service-template"]["service_template_properties"]["service_mode"] = service_mode
    if (service_type):
      js["service-template"]["service_template_properties"]["service_type"] = service_type
    if (interface_type_list):
      js["service-template"]["service_template_properties"]["interface_type"] = [{"service_interface_type": interface_type} for interface_type in interface_type_list]
    if (version):
      js["service-template"]["service_template_properties"]["version"] = version
      js["service-template"]["versionList"] = [{"text": "v{}".format(version), "id": version}]

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

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
module: virtual_machine_interface

short_description: create tungstenfabirc virtual-machine-interface

version_added: "2.9"

description:
    - "create / delete tungstenfabric virtual-machine-interface"

options:
    name:
        description:
            - virtual-machine-interface name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - virtual-machine-interface domain
        required: false
    project:
        description:
            - virtual-machine-interface project
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-machine-interface
  tungstenfabric.virtual_machine_interface.service_instance:
    name: virtual-machine-interface1
    controller_ip: x.x.x.x
    state: present

- name: delete virtual-machine-interface
  tungstenfabric.virtual_machine_interface.service_instance:
    name: virtual-machine-interface1
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
import uuid as module_uuid
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.tungstenfabric.networking.plugins.module_utils.common import login_and_check_id, crud, fqname_to_id, vnc_api_headers

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
        virtual_network=dict(type='str', required=False),
        mac_address=dict(type='str', required=False),
        disable_policy=dict(type='bool', required=False),
        allowed_address_pair=dict(type='bool', required=False)
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
    virtual_network = module.params.get("virtual_network")
    uuid = module.params.get("uuid")
    mac_address = module.params.get("mac_address")
    allowed_address_pair = module.params.get("allowed_address_pair")
    disable_policy = module.params.get("disable_policy")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='virtual-machine-interface'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)


    config_api_url = 'http://' + controller_ip + ':8082/'

    if update and state == 'present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "virtual-machine-interface":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
    )


    ## begin: object specific

    if not disable_policy == None:
      js["virtual-machine-interface"]["virtual_machine_interface_disable_policy"]=disable_policy

    if not update and mac_address:
      js["virtual-machine-interface"]["virtual_machine_interface_mac_addresses"]={"mac_address": [mac_address]}

    if not update and js["virtual-machine-interface"].get("virtual_network_refs") == None:
      vn_fqname = [domain, project, virtual_network]
      js["virtual-machine-interface"]["virtual_network_refs"]=[{"to": vn_fqname}]

    ##
    # virtual_machine_refs' attr and href need to be removed, to make webui logic work ..
    ##
    if not js["virtual-machine-interface"].get("virtual_machine_refs") == None:
      del js["virtual-machine-interface"]["virtual_machine_refs"][0]["attr"]
      del js["virtual-machine-interface"]["virtual_machine_refs"][0]["href"]


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

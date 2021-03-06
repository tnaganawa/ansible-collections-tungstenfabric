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
module: virtual_machine

short_description: create tungstenfabirc virtual-machine

version_added: "2.9"

description:
    - "create / delete tungstenfabric virtual-machine"

options:
    name:
        description:
            - virtual-machine name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - virtual-machine subnet
        required: false
    project:
        description:
            - virtual-machine subnet
        required: false
    uuid:
        description:
            - uuid of this virtual-machine
        required: true

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-machine
  tungstenfabric.networking.virtual_machine:
    name: virtual-machine1
    controller_ip: x.x.x.x
    state: present
    project: admin
    uuid: xxxx-xxxx-xxxx-xxxx

- name: delete virtual-machine
  tungstenfabric.networking.virtual_machine:
    name: virtual-machine1
    controller_ip: x.x.x.x
    state: absent
    uuid: xxxx-xxxx-xxxx-xxxx
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
        uuid=dict(type='str', required=True),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='default-project'),
        virtual_machine_interface_refs=dict(type='list', required=False)
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
    uuid = module.params.get("uuid")
    domain = module.params.get("domain")
    project = module.params.get("project")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='virtual-machine'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "virtual-machine":
        {
          "fq_name": ["%s"],
          "uuid": "%s"
        }
      }
      ''' % (name, uuid)
    )

    ## begin: object specific
    if virtual_machine_interface_refs:
      # ["default-domain:admin:vmi1"], []]
      vmi_refs_list=[]
      for vmi_fqname in virtual_machine_interface_refs:
        vmi_uuid = fqname_to_id (module, vmi_fqname, 'virtual-machine-interface', controller_ip)
        vmi_refs_list.append ({"to": vmi_fqname.split(":"), "uuid": vmi_uuid })
      js ["virtual-machine-interface"]["virtual_machine_interface_refs"]=vmi_refs_list
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

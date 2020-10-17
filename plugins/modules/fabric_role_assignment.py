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
module: fabric_role_assignment

short_description: assign a role to each fabric device 

version_added: "2.9"

description:
    - "assign a role to each fabric device"

options:
    name:
        description:
            - fabric name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - fabric subnet
        required: false
    project:
        description:
            - fabric subnet
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: assign role to each device
  tungstenfabric.networking.fabric_role_assignment:
    name: fabric1
    controller_ip: x.x.x.x
    dict_device_role:
      spine1: 
        - spine
        - CRB-Gateway, Route-Reflector
      spine2: 
        - spine
        - CRB-Gateway, Route-Reflector
      leaf1: 
        - leaf
        - CRB-Access
      leaf2: 
        - leaf
        - CRB-Access
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
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='admin'),
        dict_device_role=dict(type='dict', required=False, default='root')
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
    dict_device_role = module.params.get("dict_device_role")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='fabric'

    (web_api, update, uuid, js) = login_and_check_id(name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    ## begin: object specific
    failed=False
    config_api_url = 'http://' + controller_ip + ':8082/'
    if update:
        role_assignment_list=[]
        for device, role in dict_device_role:
          role_assignment_list.append ({"device_fq_name": device, "physical_role": role[0], "routing_bridging_roles": role[1]})
        job_input = {'fabric_fq_name': ["default-global-system-config", name],
                       'role_assignments': role_assignment_list
                    }
        payload = {'job_template_fq_name': ['default-global-system-config', 'role_assignment_template'], "job_input": job_input}
        response = requests.post(config_api_url + 'execute-job', data=json.js(payload), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
        ## TODO: wait_for for this job
    else:
        result["message"]="fabric {} doesn't exist".format(name)
    ## end: object specific


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

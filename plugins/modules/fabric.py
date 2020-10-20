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
module: fabric

short_description: create tungstenfabirc fabric

version_added: "2.9"

description:
    - "create / delete tungstenfabric fabric"

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
- name: create fabric
  tungstenfabric.networking.fabric:
    name: fabric1
    controller_ip: x.x.x.x
    state: present

- name: delete fabric
  tungstenfabric.networking.fabric:
    name: fabric1
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
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='admin'),
        device_username=dict(type='str', required=False, default='root'),
        device_password=dict(type='str', required=False, default='lab123'),
        management_subnets=dict(type='list', required=False),
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
    device_username = module.params.get("device_username")
    device_password = module.params.get("device_password")
    management_subnets = module.params.get("manamanagement_subnets")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='fabric'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    ## begin: object specific
    config_api_url = 'http://' + controller_ip + ':8082/'
    if update:
      if state == 'present':
        result["message"] = "fabric is already onboarded, nothing to do"
      elif state == 'absent':
        # delete fabric
        payload = {'job_template_fq_name': ['default-global-system-config', 'fabric_deletion_template'], "job_input": {'fabric_fq_name': ["default-global-system-config", name]}}
        response = requests.post(config_api_url + 'execute-job', data=json.js(payload), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
      else:
        module.fail_json(msg='cannot reach here', **result)
    else:
      if state == 'present'
        management_subnets_dict= [{"cidr": manamanagement_subnet } for management_subnet in management_subnets]
        job_input = {'fabric_fq_name': ["default-global-system-config", name],
                       'node_profiles': [{"node_profile_name": 'juniper-mx'}, {"node_profile_name": 'juniper-qfx10k'}, {"node_profile_name": 'juniper-qfx10k-lean'}, 
                                         {"node_profile_name": 'juniper-qfx5k'}, {"node_profile_name": 'juniper-qfx5k-lean'}, {"node_profile_name": 'juniper-srx'}]
                       'device_auth': [{"username": device_username, "password": device_password}],
                       'overlay_ibgp_asn': 64512,
                       'management_subnets': management_subnets_dict,
                       'enterprise_style': True
                   }
        payload = {'job_template_fq_name': ['default-global-system-config', 'existing_fabric_onboard_template'], "job_input": job_input}
        response = requests.post(config_api_url + 'execute-job', data=json.js(payload), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
      else:
        module.fail_json(msg='cannot reach here', **result)
    

    ## end: object specific


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

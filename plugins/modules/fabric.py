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
##
# this command can be used to see device onboard log
##
# docker exec -it analytics_api_1 contrail-logs --object-type job-execution --start-time=now-20s

- name: create fabric
  tungstenfabric.networking.fabric:
    name: fabric1
    controller_ip: x.x.x.x
    state: present
    device_username: root
    device_password: lab123
    management_subnets: [192.168.122.101/32, 192.168.122.102/32, 192.168.122.103/32, 192.168.122.104/32]
    loopback_subnets: [172.16.11.0/24]
    overlay_ibgp_asn: 64512

- name: delete fabric
  tungstenfabric.networking.fabric:
    name: fabric1
    controller_ip: x.x.x.x
    state: absent

- name: create fabric with underlay management
  tungstenfabric.networking.fabric:
    name: fabric1
    controller_ip: x.x.x.x
    state: present
    device_username: root
    device_password: lab123
    management_subnets: [192.168.122.101/32, 192.168.122.102/32, 192.168.122.103/32, 192.168.122.104/32]
    loopback_subnets: [172.16.11.0/24]
    fabric_subnets: [172.16.12.0/24]
    fabric_asn_pool: [65300, 65399]

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
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='admin'),
        device_username=dict(type='str', required=True),
        device_password=dict(type='str', required=True),
        overlay_ibgp_asn=dict(type='int', required=True),
        enterprise_style=dict(type='bool', required=False, default=True),
        management_subnets=dict(type='list', required=True),
        loopback_subnets=dict(type='list', required=True),
        fabric_subnets=dict(type='list', required=False),
        fabric_asn_pool=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["state", "present", ["device_username", "device_password"]]
    ]


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
    management_subnets = module.params.get("management_subnets")
    loopback_subnets = module.params.get("loopback_subnets")
    fabric_subnets = module.params.get("fabric_subnets")
    fabric_asn_pool = module.params.get("fabric_asn_pool")
    overlay_ibgp_asn = module.params.get("overlay_ibgp_asn")
    enterprise_style = module.params.get("enterprise_style")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='fabric'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    ## begin: object specific
    config_api_url = 'http://' + controller_ip + ':8082/'
    failed = False

    if update:
      if state == 'present':
        result["message"] = "fabric is already onboarded, nothing to do"
      elif state == 'absent':
        # delete fabric
        payload = {'job_template_fq_name': ['default-global-system-config', 'fabric_deletion_template'], "input": {'fabric_fq_name': ["default-global-system-config", name]}}
        response = requests.post(config_api_url + 'execute-job', data=json.dumps(payload), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
    else:
      if state == 'present':
        management_subnets_dict= [{"cidr": management_subnet } for management_subnet in management_subnets]
        job_input = {'fabric_fq_name': ["default-global-system-config", name],
                       'node_profiles': [{"node_profile_name": 'juniper-mx'}, {"node_profile_name": 'juniper-qfx10k'}, {"node_profile_name": 'juniper-qfx10k-lean'}, 
                                         {"node_profile_name": 'juniper-qfx5k'}, {"node_profile_name": 'juniper-qfx5k-lean'}, {"node_profile_name": 'juniper-srx'}],
                       'device_auth': [{"username": device_username, "password": device_password}],
                       'overlay_ibgp_asn': overlay_ibgp_asn,
                       'management_subnets': management_subnets_dict,
                       'loopback_subnets': loopback_subnets,
                       'enterprise_style': enterprise_style
                   }
        if fabric_subnets:
          # underlay management parameters
          job_input["fabric_subnets"]=fabric_subnets
          job_input["fabric_asn_pool"]=[{"asn_min": fabric_asn_pool[0], "asn_max": fabric_asn_pool[1]}]

        payload = {'job_template_fq_name': ['default-global-system-config', 'existing_fabric_onboard_template'], "input": job_input}
        response = requests.post(config_api_url + 'execute-job', data=json.dumps(payload), headers=vnc_api_headers)
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

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
module: loadbalancer

short_description: create tungstenfabirc loadbalancer

version_added: "2.9"

description:
    - "create / delete tungstenfabric loadbalancer"

options:
    name:
        description:
            - loadbalancer name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - loadbalancer subnet
        required: false
    project:
        description:
            - loadbalancer subnet
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
- name: create loadbalancer
  tungstenfabric.networking.loadbalancer:
    name: loadbalancer1
    controller_ip: x.x.x.x
    state: present
    project: admin
    loadbalancer_virtual_network: vn11
    loadbalancer_subnet_uuid: xxxx-xxxx-xxxx-xxxx
    loadbalancer_member_address_list: [10.0.11.11, 10.0.11.12]
    loadbalancer_member_port_list: [80, 80]
    loadbalancer_listner_protocol: TCP
    loadbalancer_listner_port: TCP
    health_monitor_delay: 5
    health_monitor_max_retries: 3
    health_monitor_monitor_type: TCP
    health_monitor_timeout: 5
    loadbalancer_pool_loadbalancer_method: LEAST_CONNECTIONS

- name: delete loadbalancer
  tungstenfabric.networking.loadbalancer:
    name: loadbalancer1
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
        loadbalancer_provider=dict(type='str', required=False, default='opencontrail', choices=['native', 'opencontrail']),
        loadbalancer_virtual_network=dict(type='str', required=False),
        loadbalancer_subnet_uuid=dict(type='str', required=False),
        loadbalancer_member_address_list=dict(type='list', required=False),
        loadbalancer_member_port_list=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["state", "present", ["loadbalancer_virtual_network", "loadbalancer_subnet_uuid", "loadbalancer_member_address_list", "loadbalancer_member_port_list"]]
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
    loadbalancer_provider = module.params.get("loadbalancer_provider")
    loadbalancer_virtual_network = module.params.get("loadbalancer_virtual_network")
    loadbalancer_subnet_uuid = module.params.get("loadbalancer_subnet_uuid")
    loadbalancer_member_address_list = module.params.get("loadbalancer_member_address_list")
    loadbalancer_member_port_list = module.params.get("loadbalancer_member_port_list")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='loadbalancer'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      {
        "loadbalancer":
          {
            "fq_name": ["%s", "%s", "%s"],
            "name": "%s",
            "loadbalancer_properties": {
              "admin_state": true,
              "vip_subnet_id": "%s"
            },
            "parent_type": "project",
            "virtual_machine_interface_refs": {
                "instance_ip_back_refs": [
                    {
                        "instance_ip_address": [
                            {
                                "domain": "%s",
                                "fixedIp": "",
                                "project": "%s"
                            }
                        ],
                        "subnet_uuid": "%s"
                    }
                ],
                "parent_type": "project",
                "virtual_machine_interface_device_owner": "neutron:LOADBALANCER",
                "virtual_network_refs": [
                    {
                        "to": [
                            "%s",
                            "%s",
                            "%s"
                        ]
                    }
                ]
            }
          }
        ,
        "loadbalancer-healthmonitor":
          {
            "fq_name": ["%s", "%s", "%s-healthmonitor"],
            "parent_type": "project",
            "loadbalancer_healthmonitor_properties": {
              "admin_state": true,
              "delay": 5,
              "timeout": 5,
              "max_retries": 3,
              "monitor_type": "TCP"
            }
          }
        ,
        "loadbalancer-listener":
          {
            "fq_name": ["%s", "%s", "%s-listener"],
            "parent_type": "project",
            "loadbalancer_listener_properties": {
              "admin_state": true,
              "connection_limit": -1,
              "protocol_port": 80,
              "protocol": "TCP"
            }
          }
        ,
        "loadbalancer-pool":
          {
            "fq_name": ["%s", "%s", "%s-pool"],
            "parent_type": "project",
            "loadbalancer_pool_properties": {
              "admin_state": true,
              "protocol": "TCP",
              "loadbalancer_method": "LEAST_CONNECTIONS"
            }
          }
      }
      ''' % (domain, project, name, name, loadbalancer_subnet_uuid, domain, project, loadbalancer_subnet_uuid, domain, project, loadbalancer_virtual_network, domain, project, name, domain, project, name, domain, project, name)
    )

    ## begin: object specific
    js["loadbalancer"]["loadbalancer_provider"] = loadbalancer_provider

    if not update:
      js["loadbalancer-member"] = []
      for i in range(len(loadbalancer_member_address_list)):
        js["loadbalancer-member"].append(
          {
            "fq_name": [domain, project, "{}-member-{}".format(name, i)],
            "parent_type": "loadbalancer-pool",
            "loadbalancer_member_properties": {
              "admin_state": True,
              "subnet_id": loadbalancer_subnet_uuid,
              "weight": 1,
              "address": loadbalancer_member_address_list[i],
              "protocol_port": loadbalancer_member_port_list[i]
            }
          }
        )

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

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
module: global_vrouter_config

short_description: create tungstenfabirc global-vrouter-config

version_added: "2.9"

description:
    - "create / delete tungstenfabric global-vrouter-config"

options:
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    flow_export_rate:
        description:
            - flow export rate from vRouter
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: update global-vrouter-config
  tungstenfabric.global_vrouter_config.global_vrouter_config:
    controller_ip: x.x.x.x
    vxlan_network_identifier_mode: configured
    encapsulation_priorities: [VXLAN, MPLSoUDP, MPLSoGRE]
    flow_export_rate: 100
    port_translation_pool: {tcp: 1023, udp: 1023}
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
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['present']),
        vxlan_network_identifier_mode=dict(type='str', required=False, choices=['automatic', 'configured']),
        encapsulation_priorities=dict(type='list', required=False),
        flow_export_rate=dict(type='int', required=False),
        port_translation_pool=dict(type='dict', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name='default-global-vrouter-config'
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    vxlan_network_identifier_mode = module.params.get("vxlan_network_identifier_mode")
    encapsulation_priorities = module.params.get("encapsulation_priorities")
    flow_export_rate = module.params.get("flow_export_rate")
    port_translation_pool = module.params.get("port_translation_pool")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='global-vrouter-config'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state)

    ## begin: object specific
    if vxlan_network_identifier_mode:
      js ["global-vrouter-config"]["vxlan_network_identifier_mode"]=vxlan_network_identifier_mode

    if encapsulation_priorities:
      js ["global-vrouter-config"]["encapsulation_priorities"]["encapsulation"]=encapsulation_priorities

    if flow_export_rate:
      js ["global-vrouter-config"]["flow_export_rate"]=flow_export_rate

    if port_translation_pool:
      port_translation_pool_list=[]
      if port_translation_pool.get("tcp"):
        port_translation_pool_list.append({"protocol": "tcp", "port_count": str(port_translation_pool.get("tcp"))})
      if port_translation_pool.get("udp"):
        port_translation_pool_list.append({"protocol": "udp", "port_count": str(port_translation_pool.get("udp"))})
      js ["global-vrouter-config"]["port_translation_pools"]={"port_translation_pool": port_translation_pool_list}

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

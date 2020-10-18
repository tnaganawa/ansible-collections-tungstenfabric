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
module: global_system_config

short_description: create tungstenfabirc global-system-config

version_added: "2.9"

description:
    - "create / delete tungstenfabric global-system-config"

options:
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    autonomous_system:
        description:
            - global AS number of this cluster
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: update global-system-config
  tungstenfabric.global_system_config.global_system_config:
    name: global-system-config1
    controller_ip: x.x.x.x
    state: present
    autonomous_system: 65001
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
        uuid=dict(type='str', required=False),
        autonomous_system=dict(type='int', required=False),
    )
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name='global-default-system-config'
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    autonomous_system = module.params.get("autonomous_system")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='global-system-config'

    (web_api, update, uuid, js) = login_and_check_id(name, obj_type, controller_ip, username, password, state)

    ## begin: object specific
    old_js = js
    js = {"global-system-config": {}}

    ## limit properties because of web api limitation
    for k in old_js["global-system-config"]:
      if k in ["bgpaas_parameters", "igmp_enable", "parent_type", "ibgp_auto_mesh", "rd_cluster_seed", "autonomous_system", "enable_4byte_as", "display_name", "plugin_tuning", "tag_refs", "id_perms:enable", "id_perms:description", "id_perms:user_visible", "id_perms:permissions", "fast_convergence_parameters", "ip_fabric_subnets", "annotations", "mac_limit_control", "user_defined_log_statistics", "config_version", "supported_vendor_hardwares", "enable_security_policy_draft", "perms2", "bgp_router_refs", "supported_fabric_annotations", "alarm_enable", "mac_move_control", "data_center_interconnect_loopback_namespace", "bgp_always_compare_med", "data_center_interconnect_asn_namespace", "graceful_restart_parameters", "supported_device_families", "mac_aging_time", "fq_name", "uuid", "display_name", "parent_type", "parent_uuid"]:
        js["global-system-config"][k]=old_js["global-system-config"][k]


    if autonomous_system:
      js ["global-system-config"]["autonomous_system"]=autonomous_system
    ## end: object specific


    payload=json.dumps(js)
    #print (payload)
    #print (js.get("global-system-config").get("uuid"))
    #sys.exit(35)

    failed = crud (web_api, controller_ip, update, state, result, payload=payload, obj_type=obj_type, uuid=uuid)


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

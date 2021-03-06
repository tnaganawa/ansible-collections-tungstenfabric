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
module: bgp_as_a_service

short_description: create tungstenfabirc bgp-as-a-service

version_added: "2.9"

description:
    - "create / delete tungstenfabric bgp-as-a-service"

options:
    name:
        description:
            - bgp-as-a-service name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - bgp-as-a-service subnet
        required: false
    project:
        description:
            - bgp-as-a-service subnet
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create bgp-as-a-service
  tungstenfabric.bgp_as_a_service.bgp_as_a_service:
    name: bgp-as-a-service1
    controller_ip: x.x.x.x
    state: present

- name: delete bgp-as-a-service
  tungstenfabric.bgp_as_a_service.bgp_as_a_service:
    name: bgp-as-a-service1
    controller_ip: x.x.x.x
    state: absent

'''

RETURN = '''
message:
    description: The output message that this module generates
    type: str
    returned: always
'''

'''
  "bgpaas_ip_address": "10.0.1.4",
  "bgpaas_ipv4_mapped_ipv6_nexthop": false,
  "bgpaas_session_attributes": {
    "address_families": {
      "family": [
        "inet"
      ]
    },
    "admin_down": false,
    "as_override": false,
    "auth_data": null,
    "family_attributes": [
      {
        "address_family": "inet",
        "prefix_limit": {
          "idle_timeout": 0,
          "maximum": 0
        }
      }
    ],
    "hold_time": 0,
    "loop_count": 0,
    "route_origin_override": {
      "origin": "IGP",
      "origin_override": false
    }
  },
  "bgpaas_shared": false,
  "bgpaas_suppress_route_advertisement": false,

  "virtual_machine_interface_refs": [
    {
      "attr": null,
      "href": "http://192.168.122.111:8082/virtual-machine-interface/94dcb507-80c4-41d5-bf6e-01137d359a63",
      "to": [
        "default-domain",
        "admin",
        "94dcb507-80c4-41d5-bf6e-01137d359a63"
      ],
      "uuid": "94dcb507-80c4-41d5-bf6e-01137d359a63"
    }
  ]

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
        bgpaas_ip_address=dict(type='str', required=False),
        hold_time=dict(type='int', required=False, default=90),
        address_families=dict(type='list', required=False, default=['inet']),
        autonomous_system=dict(type='int', required=True),
        virtual_machine_interface_refs=dict(type='str', required=False)
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
    address_families = module.params.get("address_families")
    autonomous_system = module.params.get("autonomous_system")
    bgpaas_ip_address = module.params.get("bgpaas_ip_address")
    hold_time = module.params.get("hold_time")
    virtual_machine_interface_refs = module.params.get("virtual_machine_interface_refs")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='bgp-as-a-service'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)


    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "bgp-as-a-service":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
    )

    ## begin: object specific
    if autonomous_system:
      js ["bgp-as-a-service"]["autonomous_system"]=autonomous_system
    if bgpaas_ip_address:
      js ["bgp-as-a-service"]["bgpaas_ip_address"]=bgpaas_ip_address

    if js ["bgp-as-a-service"].get("bgpaas_session_attributes") == None:
      js ["bgp-as-a-service"]["bgpaas_session_attributes"]={}
      if address_families:
        js ["bgp-as-a-service"]["bgpaas_session_attributes"]["address_families"]={"family": address_families}
      if hold_time:
        js ["bgp-as-a-service"]["bgpaas_session_attributes"]["hold_time"]=hold_time
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

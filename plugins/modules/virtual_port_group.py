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
module: virtual_port_group

short_description: create tungstenfabirc virtual-port-group

version_added: "2.9"

description:
    - "create / delete tungstenfabric virtual-port-group"

options:
    name:
        description:
            - virtual-port-group name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    domain:
        description:
            - domain for this vpg
        required: false
    project:
        description:
            - project for this vpg
        required: false
    fabric:
        description:
            - fabric for this vpg
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-port-group
  tungstenfabric.networking.virtual_port_group:
    name: virtual-port-group1
    controller_ip: x.x.x.x
    state: present
    physical_interfaces:
      - [leaf1, xe-0/0/3]
      - [leaf2, xe-0/0/3]

- name: delete virtual-port-group
  tungstenfabric.networking.virtual_port_group:
    name: virtual-port-group1
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
        fabric=dict(type='str', required=True),
        physical_interfaces=dict(type='list', required=False)
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
    fabric = module.params.get("fabric")
    physical_interfaces = module.params.get("physical_interfaces")

    if module.check_mode:
        module.exit_json(**result)

    obj_type='virtual-port-group'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project, fabric=fabric)

    ## begin: object specific
    config_api_url = 'http://' + controller_ip + ':8082/'
    vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}

    failed=False


    ## create physical_interface_refs when physical_interface is not empty
    physical_interface_refs=[]
    if state == 'present' and physical_interfaces:
        for device, physical_interface in physical_interfaces:

          # get uuid of physical-interface
          response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "physical_interface", "fq_name": ["default-global-system-config", "%s", "%s"]}' % (device, physical_interface), headers=vnc_api_headers)
          if not response.status_code == 200:
            failed = True
            result["message"] = response.text
            module.fail_json(msg="physical-interface doesn't exist", **result)
          pi_uuid = json.loads(response.text).get("uuid")

          physical_interface_refs.append({"uuid": pi_uuid, "to": ["default-global-config", device, physical_interface], "attr": None})

    if update:
      if state == 'present':
        # add physical-interfaces
        js["virtual-port-group"]["physical_interface_refs"]=physical_interface_refs
        response = requests.put(config_api_url + 'virtual-port-group/' + uuid, data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="physical interface addition failed", **result)

      elif state == 'absent':
        # delete virtual-port-group
        response = requests.delete(config_api_url + 'virtual-port-group/' + uuid, data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="vpg deletion failed", **result)
    else:
      if state == 'present':
        js=json.loads (
        '''
        { "virtual-port-group":
          {
            "fq_name": ["default-global-system-config", "%s", "%s"],
            "parent_type": "fabric"
          }
        }
        ''' % (fabric, name)
        )
        response = requests.post(config_api_url + 'virtual-port-groups', data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="vpg creation failed", **result)

        # add physical-interfaces
        uuid = json.loads(response.text).get("virtual-port-group").get("uuid")

        js["virtual-port-group"]["physical_interface_refs"]=physical_interface_refs

        response = requests.put(config_api_url + 'virtual-port-group/' + uuid, data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="physical interface addition failed", **result)

      else:
        module.fail_json(msg="vpg doesn't exist", **result)


    ## end: object specific


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

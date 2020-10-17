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
module: bms_vmi

short_description: add vlan / vn pair to vpg

version_added: "2.9"

description:
    - "add vlan / vn pair to vpg"

options:
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    vpg_vn_vlan_list:
        description:
            - list of vpg / vn / vlan-id tuple
        required: true
    domain:
        description:
            - domain for this vpg and vmi
        required: false
    project:
        description:
            - project for this vpg and vmi
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-port-group
  tungstenfabric.networking.bms_vmi:
    controller_ip: x.x.x.x
    state: present
    vpg_vn_vlan_list:
     - [virtual-port-group1, vn1, 101]
     - [virtual-port-group1, vn2, 102]
     - [virtual-port-group2, vn1, 101]

- name: delete virtual-port-group
  tungstenfabric.networking.bms_vmi:
    controller_ip: x.x.x.x
    state: absent
    vpg_vn_vlan_list:
     - [virtual-port-group1, vn1, 101]
     - [virtual-port-group1, vn2, 102]
     - [virtual-port-group2, vn1, 101]
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
from ansible_collections.tungstenvirtual-port-group.networking.plugins.module_utils.common import login_and_check_id, crud

def run_module():
    module_args = dict(
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='admin'),
        vpg_vn_vlan_list=dict(type='list', required=True)
    )
    result = dict(
        changed=False,
        message=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    name = "dummy"
    controller_ip = module.params.get("controller_ip")
    username = module.params.get("username")
    password = module.params.get("password")
    state = module.params.get("state")
    domain = module.params.get("domain")
    project = module.params.get("project")
    vpg_vn_vlan_list = module.params.get("vpg_vn_vlan_list")

    if module.check_mode:
        module.exit_json(**result)


    ## begin: object specific
    config_api_url = 'http://' + controller_ip + ':8082/'

    for vpg_name, vn_name, vlan_id in vpg_vn_vlan_list:

      ## check if the fqname exists
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "virtual-port-group", "fq_name": ["%s", "%s", "%s"]}' % (domain, project, vpg_name), headers=vnc_api_headers)
      if response.status_code == 200:
        tmp = json.loads(response.text)
        vpg_uuid = tmp.get("uuid")

        response = requests.get(config_api_url + 'virtual-machine-interface/' + vpg_uuid, headers=vnc_api_headers)
        vpg_vmi_refs = json.loads(response.text).get("virtual_machine_interface_refs")
      else:
        failed = True
        result["message"] = response.text
        module.fail_json(msg="cannot assign / delete vlan-id / vn pair, since vpg is not available", **result)

      if state == 'present':
        # check virtual-network uuid
        response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "virtual-network", "fq_name": ["%s", "%s", "%s"]}' % (domain, project, vn_name), headers=vnc_api_headers)
        if response.status_code == 200:
          vn_uuid = json.loads(response.text).get("uuid")
        else:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="cannot assign / delete vlan-id / vn pair, since vpg is not available", **result)

        # create vmi with vpg_uuid, vn_uuid and vlan-id
        js=json.loads (
        '''
        { "virtual-machine-interface":
          {
            "fq_name": ["%s", "%s", "%s"],
            "parent_type": "project",
            "device_owner": "baremetal:None",
            "virtual_machine_interface_bindings": {
              "vnic_type": "baremetal",
              "vpg": "%s",
              "profile": {"local_link_information": {"fabric": "", "switch_info": "", "port_id": ""}}
            },
            "virtual_network_refs": [
             {
             "to": ["%s", "%s", "%s"],
             "uuid": "%s",
             }
            ],
            "sub_inteface_vlan_tag": "%s"
          }
        }
        ''' % (domain, project, "".join (vpg_name, '-', project, '-', vn_name, '-', str(vlan_id)), vpg_name, domain, project, vn_name, vn_uuid, vlan_id)
        )
        response = requests.post(config_api_url + 'virtual-machine-interfaces', data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="vlan / vn assignment failed", **result)

      elif state == 'absent':
        # check vpg's virtual_machine_interface refs and get attr vlan_tag
        vmi_uuid=''
        for vmi_ref in vpg_vmi_refs:
          if vlan_id == vmi_ref.get("attr").get("sub_inteface_vlan_tag"):
            vmi_uuid = vmi_ref.get("uuid")
        if vmi_uuid=='':
          failed = True
          module.fail_json(msg="cannot find vmi_uuid to be deleted", **result)

        # delete virtual-machine-interfaces
        response = requests.delete(config_api_url + 'virtual-machine-interfaces/' + vmi_uuid, headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="vn / vlan-id pair deletion failed", **result)
    ## end: object specific


    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

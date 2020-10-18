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
    domain:
        description:
            - domain for this vpg and vmi
        required: false
    project:
        description:
            - project for this vpg and vmi
        required: false
    vpg_vn_vlan_list:
        description:
            - list of vpg / vn / vlan-id tuple
        required: true

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-port-group
  tungstenfabric.networking.bms_vmi:
    controller_ip: x.x.x.x
    state: present
    project: admin
    vpg_vn_vlan_list:
     - [virtual-port-group1, vn1, 101]
     - [virtual-port-group1, vn2, 102]
     - [virtual-port-group2, vn1, 101]

- name: delete virtual-port-group
  tungstenfabric.networking.bms_vmi:
    controller_ip: x.x.x.x
    state: absent
    project: admin
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
from ansible_collections.tungstenfabric.networking.plugins.module_utils.common import login_and_check_id, crud

def run_module():
    module_args = dict(
        controller_ip=dict(type='str', required=True),
        username=dict(type='str', required=False, default='admin'),
        password=dict(type='str', required=False, default='contrail123'),
        state=dict(type='str', required=False, default='present', choices=['absent', 'present']),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='admin'),
        fabric=dict(type='str', required=True),
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
    fabric = module.params.get("fabric")
    vpg_vn_vlan_list = module.params.get("vpg_vn_vlan_list")

    if module.check_mode:
        module.exit_json(**result)


    ## begin: object specific
    config_api_url = 'http://' + controller_ip + ':8082/'
    vnc_api_headers= {"Content-Type": "application/json", "charset": "UTF-8"}

    failed=False

    for vpg_name, vn_name, vlan_id in vpg_vn_vlan_list:

      ## check if the vpg exists
      response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "virtual-port-group", "fq_name": ["default-global-system-config", "%s", "%s"]}' % (fabric, vpg_name), headers=vnc_api_headers)
      if response.status_code == 200:
        tmp = json.loads(response.text)
        vpg_uuid = tmp.get("uuid")

        response = requests.get(config_api_url + 'virtual-port-group/' + vpg_uuid, headers=vnc_api_headers)
        vpg_vmi_refs = json.loads(response.text).get("virtual-port-group").get("virtual_machine_interface_refs")
        physical_interface_refs = json.loads(response.text).get("virtual-port-group").get("physical_interface_refs")

        if response.status_code == 200:
          pass
        else:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="cannot get vpg detail", **result)
      else:
        failed = True
        result["message"] = response.text
        module.fail_json(msg="cannot assign / delete vlan-id / vn pair, since vpg is not available", **result)

      if state == 'present':
        # TODO:
        # check vpg's virtual_machine_interface refs and get attr vlan_tag
        # annotation or virtual_machine_interface_refs' attr
        # skip this if already available

        # check virtual-network uuid
        response = requests.post(config_api_url + 'fqname-to-id', data='{"type": "virtual-network", "fq_name": ["%s", "%s", "%s"]}' % (domain, project, vn_name), headers=vnc_api_headers)
        if response.status_code == 200:
          vn_uuid = json.loads(response.text).get("uuid")
        else:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="cannot assign / delete vlan-id / vn pair, since vn is not available", **result)

        # local link information: please make them the same with vpg side definition, since this definition will update VPG pi refs ..
        local_link_information_list=[]
        for pi_refs in physical_interface_refs:
          port_id=pi_refs.get("to")[2]
          switch_info=pi_refs.get("to")[1]
          local_link_information_list.append({"fabric": fabric, "switch_info": switch_info, "port_id": port_id})
        local_link_information_str=json.dumps({"local_link_information": local_link_information_list})

        # create vmi with vpg_uuid, vn_uuid and vlan-id
        tmp_str = '''
        { "virtual-machine-interface":
          {
            "fq_name": ["%s", "%s", "%s"],
            "parent_type": "project",
            "device_owner": "baremetal:None",
            "virtual_machine_interface_bindings": {
              "key_value_pair": [
                {"key": "vpg", "value": "%s"},
                {"key": "vnic_type", "value": "baremetal"},
                {"key": "vif_type", "value": "vrouter"}
              ]
            },
            "virtual_network_refs": [
             {
             "to": ["%s", "%s", "%s"],
             "uuid": "%s"
             }
            ],
            "virtual_machine_interface_properties": {
              "sub_interface_vlan_tag": %s
            }
          }
        }
        ''' % (domain, project, "".join ((vpg_name, '-', fabric, '-', vn_name, '-', str(vlan_id))), vpg_name, domain, project, vn_name, vn_uuid, vlan_id)

        js=json.loads (tmp_str)
        js["virtual-machine-interface"]["virtual_machine_interface_bindings"]["key_value_pair"].append({"key": "profile", "value": local_link_information_str})


        response = requests.post(config_api_url + 'virtual-machine-interfaces', data=json.dumps(js), headers=vnc_api_headers)
        if not response.status_code == 200:
          failed = True
          result["message"] = response.text
          module.fail_json(msg="vlan / vn assignment failed", **result)

      elif state == 'absent':
        # TODO:
        # check vpg's virtual_machine_interface refs and get attr vlan_tag
        # annotation or virtual_machine_interface_refs' attr
        # skip this if already available
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

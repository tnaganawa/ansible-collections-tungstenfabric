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
module: virtual_network

short_description: create tungstenfabirc virtual-network

version_added: "2.10"

description:
    - "create / delete tungstenfabric virtual-network"

options:
    name:
        description:
            - virtual-network name
        required: true
    controller_ip:
        description:
            - tungstenfabric controller ip
        required: true
    subnet:
        description:
            - virtual-network subnet
        required: false
    subnet_prefix:
        description:
            - virtual-network subnet prefix
        required: false
    addr_from_start:
        description:
            - when it is set to true, subnet address is assigned from .1, .2, ... and if it is set to false, .254, .253, ... will be used (Default: false)
        required: false
    default_gateway:
        description:
            - ip address for default gateway served by vRouter
        required: false
    dns_server_address:
        description:
            - ip address for dns_server_address served by vRouter
        required: false
    enable_dhcp:
        description:
            - if it is set to true,  dhcp is served by vRouter (Default: true)
        required: false
    dns_nameservers:
        description:
            - list of nameservers
        required: false
    domain:
        description:
            - virtual-network subnet
        required: false
    project:
        description:
            - virtual-network subnet
        required: false
    forwarding_mode:
        description:
            - set forwarding mode (L2_L3, L2, L3)
        required: false
    rpf:
        description:
            - set rpf (enable or disable)
        required: false
    allow_transit:
        description:
            - set allow_transit (true or false)
        required: false
    vxlan_network_identifier:
        description:
            - set vni of this virtual-network
        required: false
    route_target_list:
        description:
            - list of route-target
        required: false
    import_route_target_list:
        description:
            - list of import route-target
        required: false
    export_route_target_list:
        description:
            - list of export route-target
        required: false
    network_policy_refs:
        description:
            - set network-policy (fq_name of network-policy)
        required: false
    virtual_network_category:
        description:
            - routed VN or Switched VN (used only by fabric-manager)
        required: false
    routed_properties_logical_router_name:
        description:
            - logical-router name for this routed VN
        required: false
    routed_properties_physical_router_name_list:
        description:
            - physical-router name for this routed properties
        required: false
    routed_properties_routed_interface_ip_address_list:
        description:
            - logical-router name for this routed VN
        required: false
    routed_properties_routing_protocol_list:
        description:
            - routing-protocol (static / ospf / eBGP)
        required: false
    routed_properties_routing_protocol_ospf_params_area_id_list:
        description:
            - area id  of ospf from routed VN
        required: false
    provider_network:
        description:
            - bool to use this VN as provider-network (default: false)
        required: false
    provider_network_physical_network:
        description:
            - physical network which this VN is associated to
        required: false
    provider_network_segmentation_id:
        description:
            - provider network segmentation id which this VN is associated to
        required: false

author:
    - Tatsuya Naganawa (@tnaganawa)
'''

EXAMPLES = '''
# Pass in a message
- name: create virtual-network
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: present
    project: admin
    subnet: 10.0.1.0
    subnet_prefix: 24

- name: delete virtual-network
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: absent
    project: admin

- name: create virtual-network with some parameters
  tungstenfabric_virtual_network:
    name: vn1
    controller_ip: x.x.x.x
    state: present
    project: admin
    subnet: 10.0.1.0
    subnet_prefix: 24
    addr_from_start: true
    default_gateway: 10.0.1.1
    dns_nameserver: 10.0.1.2
    enable_dhcp: true
    rpf: enable
    vxlan_network_identifier: 101
    route_target_list: [target:64512:101, target:65501:101]
    network_policy_refs: [default-domain:admin:vn1-to-vn2]

- name: create virtual-network as provider network for SR-IOV NIC
  tungstenfabric_virtual_network:
    name: vn-physnet1
    controller_ip: x.x.x.x
    state: present
    project: admin
    provider_network: true
    provider_network_physical_network: physnet1
    provider_network_segmentation_id: 100

'''

RETURN = '''
message:
    description: The output message that this module generates
    type: str
    returned: always
'''

import sys
import uuid as uuid_module
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
        global_object=dict(type='bool', required=False),
        uuid=dict(type='str', required=False),
        domain=dict(type='str', required=False, default='default-domain'),
        project=dict(type='str', required=False, default='default-project'),
        subnet=dict(type='str', required=False),
        subnet_prefix=dict(type='int', required=False),
        addr_from_start=dict(type='bool', required=False, default=False),
        default_gateway=dict(type='str', required=False),
        dns_server_address=dict(type='str', required=False),
        enable_dhcp=dict(type='bool', required=False),
        dns_nameservers=dict(type='list', required=False),
        flood_unknown_unicast=dict(type='bool', required=False),
        ip_fabric_forwarding=dict(type='bool', required=False),
        fabric_snat=dict(type='bool', required=False),
        display_name=dict(type='str', required=False),
        igmp_enable=dict(type='bool', required=False),
        mac_learning_enabled=dict(type='bool', required=False),
        port_security_enabled=dict(type='bool', required=False),
        allow_transit=dict(type='bool', required=False),
        forwarding_mode=dict(type='str', required=False, choices=['default', 'l2_l3', 'l3', 'l2']),
        max_flows=dict(type='int', required=False),
        rpf=dict(type='str', required=False, choices=['enable', 'disable']),
        vxlan_network_identifier=dict(type='int', required=False),
        route_target_list=dict(type='list', required=False),
        import_route_target_list=dict(type='list', required=False),
        export_route_target_list=dict(type='list', required=False),
        virtual_network_category=dict(type='str', required=False, choices=['routed']),
        network_policy_refs=dict(type='list', required=False),
        provider_network=dict(type='bool', required=False, default=False),
        provider_network_physical_network=dict(type='str', required=False),
        provider_network_segmentation_id=dict(type='int', required=False),
        tag_refs=dict(type='list', required=False)
    )
    result = dict(
        changed=False,
        message=''
    )

    required_if_args = [
      ["global_object", True, ["domain", "project", "name", "route_target_list", "vxlan_network_identifier"]],
      ["provider_network", True, ["provider_network_physical_network", "provider_network_segmentation_id"]]
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
    subnet = module.params.get("subnet")
    subnet_prefix = module.params.get("subnet_prefix")
    addr_from_start = module.params.get("addr_from_start")
    default_gateway = module.params.get("default_gateway")
    dns_server_address = module.params.get("dns_server_address")
    enable_dhcp = module.params.get("enable_dhcp")
    dns_nameservers = module.params.get("dns_nameservers")
    flood_unknown_unicast = module.params.get("flood_unknown_unicast")
    ip_fabric_forwarding = module.params.get("ip_fabric_forwarding")
    fabric_snat = module.params.get("fabric_snat")
    rpf = module.params.get("rpf")
    allow_transit = module.params.get("allow_transit")
    forwarding_mode = module.params.get("forwarding_mode")
    vxlan_network_identifier = module.params.get("vxlan_network_identifier")
    route_target_list = module.params.get("route_target_list")
    import_route_target_list = module.params.get("import_route_target_list")
    export_route_target_list = module.params.get("export_route_target_list")
    virtual_network_category = module.params.get("virtual_network_category")
    network_policy_refs = module.params.get("network_policy_refs")
    provider_network = module.params.get("provider_network")
    provider_network_physical_network = module.params.get("provider_network_physical_network")
    provider_network_segmentation_id = module.params.get("provider_network_segmentation_id")
    tag_refs = module.params.get("tag_refs")

    if module.check_mode:
        module.exit_json(**result)

    ## begin: virtual-network
    config_api_url = 'http://' + controller_ip + ':8082/'

    obj_type='virtual-network'

    (web_api, update, uuid, js) = login_and_check_id(module, name, obj_type, controller_ip, username, password, state, domain=domain, project=project)

    if update and state=='present':
      pass
    else:
      ## create payload and call API
      js=json.loads (
      '''
      { "virtual-network":
        {
          "fq_name": ["%s", "%s", "%s"],
          "parent_type": "project"
        }
      }
      ''' % (domain, project, name)
      )

    if subnet:
      if (js["virtual-network"].get("network_ipam_refs")==None):
        js ["virtual-network"]["network_ipam_refs"]=[
          {"to": ["default-domain", "default-project", "default-network-ipam"],
            "attr": {"ipam_subnets":
              [
                {"subnet":
                  {"ip_prefix": subnet, "ip_prefix_len": subnet_prefix}
                }
              ]
            }
          }
        ]
        subnet_uuid=str(uuid_module.uuid4())
        js ["virtual-network"]["network_ipam_refs"][0]["attr"]["ipam_subnets"][0]["subnet_uuid"]=subnet_uuid
        js ["virtual-network"]["network_ipam_refs"][0]["attr"]["ipam_subnets"][0]["subnet_name"]=subnet_uuid

        subnet_param = js ["virtual-network"]["network_ipam_refs"][0]["attr"]["ipam_subnets"][0]
        if not addr_from_start == None:
          subnet_param["addr_from_start"]=addr_from_start
        if not default_gateway == None:
          subnet_param["default_gateway"]=default_gateway
        if not dns_server_address == None:
          subnet_param["dns_server_address"]=dns_server_address
        if not enable_dhcp == None:
          subnet_param["enable_dhcp"]=enable_dhcp
        if not dns_nameservers == None:
          subnet_param["dhcp_option_list"]={"dhcp_option": [{"dhcp_option_name": "6", "dhcp_option_value": " ".join(dns_nameservers)}]}

    if flood_unknown_unicast:
      js ["virtual-network"]["flood_unknown_unicast"]=True
    if ip_fabric_forwarding:
      js ["virtual-network"]["ip_fabric_forwarding"]=True
    if fabric_snat:
      js ["virtual-network"]["fabric_snat"]=True
    if virtual_network_category:
      js ["virtual-network"]["virtual_network_category"]=virtual_network_category
    if not network_policy_refs == None:
      # ["default-domain:admin:network-policy1"], []]
      network_policy_refs_list=[]
      for np_fqname in network_policy_refs:
        response = requests.post(config_api_url + 'fqname-to-id', data=json.dumps({"type": "network-policy", "fq_name": np_fqname.split(":")}), headers=vnc_api_headers)
        if not response.status_code == 200:
          module.fail_json(msg="network-policy specified doesn't exist", **result)
        np_uuid = json.loads(response.text).get("uuid")
        network_policy_refs_list.append ({"to": np_fqname.split(":"), "uuid": np_uuid, "attr": {"sequence": {"major": 0, "minor": 0}}})
      js ["virtual-network"]["network_policy_refs"]=network_policy_refs_list
    if provider_network:
      if js["virtual-network"].get("provider_properties")==None:
        js ["virtual-network"]["provider_properties"]={}
      js ["virtual-network"]["provider_properties"]["physical_network"]=provider_network_physical_network
      js ["virtual-network"]["provider_properties"]["segmentation_id"]=provider_network_segmentation_id

    if not tag_refs == None:
      # ["default-domain:admin:site=A"], []]
      tag_refs_list=[]
      for tag_fqname in tag_refs:
        tag_uuid = fqname_to_id (module, tag_fqname, 'tag', controller_ip)
        tag_refs_list.append ({"to": tag_fqname.split(":"), "uuid": tag_uuid })
      js ["virtual-network"]["tag_refs"]=tag_refs_list


    if js["virtual-network"].get("virtual_network_properties")==None:
      js ["virtual-network"]["virtual_network_properties"]={}
    if rpf:
      js ["virtual-network"]["virtual_network_properties"]["rpf"]=rpf
    if allow_transit:
      js ["virtual-network"]["virtual_network_properties"]["allow_transit"]=allow_transit
    if forwarding_mode:
      js ["virtual-network"]["virtual_network_properties"]["forwarding_mode"]=forwarding_mode
    if vxlan_network_identifier:
      js ["virtual-network"]["virtual_network_properties"]["vxlan_network_identifier"]=vxlan_network_identifier
    if route_target_list:
      js ["virtual-network"]["route_target_list"]={"route_target": route_target_list}
    if import_route_target_list:
      js ["virtual-network"]["import_route_target_list"]={"route_target": import_route_target_list}
    if export_route_target_list:
      js ["virtual-network"]["export_route_target_list"]={"route_target": export_route_target_list}

    ## end: virtual-network


    payload=json.dumps(js)

    failed = crud (web_api, controller_ip, update, state, result, payload=payload, obj_type=obj_type, uuid=uuid)

    if failed:
        module.fail_json(msg='failure message', **result)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()

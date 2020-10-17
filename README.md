# ansible-collections-tungstenfabric
ansible module for tungstenfabric


### Install
```
cd
pip install virtualenv
virtualenv venv
source venv/bin/activate
pip install ansible requests


git clone https://github.com/tnaganawa/ansible-collections-tungstenfabric.git
mkdir -p ~/.ansible/collections/ansible_collections/tungstenfabric/networking/
mv -i ansible-collections-tungstenfabric/plugins/ ~/.ansible/collections/ansible_collections/tungstenfabric/networking/
 or
ansible-galaxy collection install git+https://github.com/tnaganawa/ansible-collections-tungstenfabric.git
```

 - For ansible collentions to work, ansible 2.9 or later is required.

### from CLI
```
create:
ansible -m tungstenfabric.networking.virtual_network localhost -a 'name=vn1 controller_ip=x.x.x.x state=present'

update:
ansible -m tungstenfabric.networking.virtual_network localhost -a 'name=vn1 controller_ip=x.x.x.x state=present subnet=10.0.1.0 subnet_prefix=24'

delete:
ansible -m tungstenfabric.networking.virtual_network localhost -a 'name=vn1 controller_ip=x.x.x.x state=absent'
```

### from playbook

```
# cat virtual-port-group.yaml
- name: create vpg
  hosts: localhost
  tasks:
  - name: create vpg
    tungstenfabric.networking.virtual_port_group:
      name: vpg1
      controller_ip: x.x.x.x
      state: present
      fabric: fabric1
      physical_interfaces:
        - [leaf1, xe-0/0/9]
        - [leaf2, xe-0/0/9]

# cat bms_vmi.yaml
- name: add vn vlan pair
  hosts: localhost
  tasks:
  - name: add vn vlan pair
    tungstenfabric.networking.bms_vmi:
      controller_ip: x.x.x.x
      state: present
      fabric: fabric1
      vpg_vn_vlan_list:
       - [vpg1, vn111, 111]
       - [vpg1, vn112, 112]

# ansible-playbook -i localhost virtual-port-group.yaml
# ansible-playbook -i localhost bms_vmi.yaml
```

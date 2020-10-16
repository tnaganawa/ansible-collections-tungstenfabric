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


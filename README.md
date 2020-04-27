# ipapi

## installation on centos 7

### install, enable and start mongodb
```
echo "[mongodb-org-4.2]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/7/mongodb-org/4.2/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.2.asc" > /etc/yum.repos.d/mongodb-org-4.2.repo

yum install mongodb-org
systemctl enable mongod
systemctl start mongod
```

### install epel-release, python36 and pip; upgrade pip3.6
```
yum install epel-release
yum install python36 #python3
yum install python36-pip #python3-pip
pip install --upgrade pip
```

### install gcc and python36-devel for uwsgi
```
yum install gcc
yum install python36-devel #python3-devel
```

### git clone ipapi; cd ipapi
```
git clone https://github.com/odrolit/ipapi
cd ipapi
```

### virtualenv install, create and activate
```
pip install virtualenv
virtualenv venv
source venv/bin/activate
```

### install requirements
```
pip install -r requirements.txt
```

Steps to renew/change the OpenVPN CA and keys:

- Run a docker container mounting this directory to /etc/openvpn/
- apt-get install easy-rsa3
- cd /etc/openvpn
- easyrsa init-pki
- easyrsa build-ca nopass
- export EASYRSA_CERT_EXPIRE=8501
- easyrsa build-server-full race nopass
- easyrsa build-client-full race-client nopass
- Copy appropriate keys and certificates to override those in race-client.ovpn

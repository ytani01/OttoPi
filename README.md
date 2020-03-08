# OttoPi

Otto like biped robot for Raspberry Pi Zero

## 1. Install

### 1.1 start pigpiod

```bash
$ sudo pigpiod
```


### 1.2 install pipenv

```bash
$ sudo pip3 install -U pip
$ hash -r

$ sudo pip3 install pipenv

$ pipenv install
```


## 2. Uninstall

### 2.1 remove virtualenv

```bash
$ pipenv --rm
```


## 3. run command in virtualenv

```bash
$ pipenv run COMMAND [ARG] ..
```

## 4. enter into virtualenv

```bash
$ pipenv shell
(venv) $
```

### 4.1 exit from virtualenv

```bash
(venv) $ exit
$
```


## A.1 証明書

### 自己証明書

```bash
$ openssl req -new -x509 -days 3650 -nodes -out cert.pem -keyout cert.pem
```


### 作成した証明書の確認

```bash
$ openssl x509 -text -noout -in ./cert.pem | less
```


### サーバー名が複数のIPアドレスの場合

``mycert.cnf``
```
[ req ]
default_bits = 2048
default_md = sha256
prompt = no
encrypt_key = no
distinguished_name = dn
req_extensions = v3_req

[ dn ]
C = JP
O = Private
CN = $SERVER_NAME

[ v3_req ]
subjectAltName = @alt_names

[ alt_names ]
IP.1 = $IP_ADDRESS
# マルチドメイン用の証明書の場合
#DNS.1 = example.com
#DNS.2 = www.example.com
#DNS.3 = hoge.example.com
#DNS.4 = fuga.example.com
```
```bash
$ openssl req -new -x509 -config mycert.cnf-days 3650 -nodes -extensions v3_req -out cert.pem -keyout cert.pem
```


## References

- [+OttoDIY / otto-diy-laser-cut](https://wikifactory.com/+OttoDIY/otto-diy-laser-cut)

- [Adding Basic Audio Output to Raspberry Pi Zero](https://learn.adafruit.com/adding-basic-audio-ouput-to-raspberry-pi-zero/pi-zero-pwm-audio)

- [Python - ssl](https://docs.python.org/ja/3/library/ssl.html#certificates)

- [サーバ名がIPアドレスの場合のSSL証明書作成](https://www.magata.net/memo/index.php?%A5%B5%A1%BC%A5%D0%CC%BE%A4%ACIP%A5%A2%A5%C9%A5%EC%A5%B9%A4%CE%BE%EC%B9%E7%A4%CESSL%BE%DA%CC%C0%BD%F1%BA%EE%C0%AE)

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

## References

- [+OttoDIY / otto-diy-laser-cut](https://wikifactory.com/+OttoDIY/otto-diy-laser-cut)
- [Adding Basic Audio Output to Raspberry Pi Zero](https://learn.adafruit.com/adding-basic-audio-ouput-to-raspberry-pi-zero/pi-zero-pwm-audio)

# OttoPi: Otto DIY like biped robot for Raspberry Pi (Zero)

see [github pages](https://ytani01.github.io/OttoPi/)

## ToDo

### Power ON button

GPIO 3 -> SW -> GND

### Shutdown button

GPIO 4 -> SW -> GND
GPIO 21 -> R(1K ohm) -> LED -> GND

```
dtoverlay=gpio-shutdown,gpio_pin=4
dtoverlay=gpio-poweroff,gpiopin=21,active_low=1
```

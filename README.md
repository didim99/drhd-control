# drhd-control

This utility intended for control `Dr.HD MA 444 FSE 50`
HDMI 4x4 matrix over TCP/IP.

## Config file format

[Test script](test.py) uses JSON file named `config.json` with
following structure:

```json
{
  "bind_to": "192.168.0.100",
  "device": "192.168.0.10",
  "device_mac": "ff:ff:ff:ff:ff:ff",
  "log_udp": "debug",
  "log_tcp": "debug",
  "num_req": 3
}
```

where:
* `bind_to` (`string`) - local IP address to bind for discovery
* `device` (`string`) - IP address of matrix (if known)
* `device_mac` (`string`) - MAC address of matrix (if IP can't be used)
* `log_udp` (`string`) - logging level for UDP discovery
* `log_tcp` (`string`) - logging level for TCP communication
* `num_req` (`int`) - number of requests when scanning for devices

## Protocol info

* Port `30600/UDP` used for discovery
* Port `8000/TCP` used for matrix control

### Network discovery

To find matrix in local network send single byte `0x61` to
global broadcast ip `255.255.255.255` and UDP port `30600`.
Reply packet will be sent to your local IP and UDP port `30600`.

Reply packet structure (55 bytes total):
```
6 bytes  - device MAC
4 bytes  - device IP
4 bytes  - gateway IP
4 bytes  - subnet mask
2 bytes  - port number (30600) in big-endian
2 bytes  - constant (?) 80 in big-endian
32 bytes - placeholder (?) zero-bytes
1 byte   - constant (?) 0x01
```

# GhostKVM

GhostKVM is a software-based, cross-platform KVM solution that automatically switches monitor inputs (via DDC/CI) when a keyboard is disconnected. Perfect for sharing a monitor between two computers without a physical switch.

## Installation

### 1. Prerequisites
You need tools to send DDC/CI commands:
- **Linux:** Install ddcutil: `sudo apt install ddcutil`.

### 2. Install Dependencies
```bash
pip3 install -r requirements.txt
```
### 3. Configuration
Open ghost_kvm.py and change INPUT_CODE to match your monitor's input (e.g., 0x0f for DisplayPort).

## Linux (systemd)
Create /etc/systemd/system/ghost-kvm.service:

```Ini, TOML
[Unit]
Description=GhostKVM Daemon
After=network.target

[Service]
ExecStart=/usr/bin/python3 /path/to/ghost_kvm.py
Environment=DISPLAY=:0
Restart=always
User=your_username

[Install]
WantedBy=multi-user.target 
```

Activate with:
```bash
sudo systemctl daemon-reload
sudo systemctl enable ghost-kvm --now
``
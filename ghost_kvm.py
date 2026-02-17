import platform
import subprocess
import sys
import time
import os
#import pyautogui

# --- INSTÄLLNINGAR ---
# Ändra dessa koder så de matchar din setup
# För Linux (ddcutil): Använd '0x0f', '0x11' etc.
# För Windows (monitorcontrol): Använd siffror (t.ex. "1" för första källan) eller hex.
INPUT_CODE = "0x0f" 
DEBOUNCE_TIME = 3 # Sekunder att vänta innan nästa switch tillåts

last_switch_time = 0

def log(msg):
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {msg}")
    sys.stdout.flush()

def wake_pc():
    os_type = platform.system()
    if os_type == "Windows":
        try:
            import pyautogui
            pyautogui.press('shift')
        except: pass
        
    elif os_type == "Linux":
        # 1. Försök med loginctl (fungerar på de flesta systemd-distros)
        # Detta väcker sessionen och kan låsa upp skärmsläckaren
        try:
            subprocess.run(["loginctl", "unlock-session"], capture_output=True)
        except: pass

        # 2. Miljöspecifika "pokes"
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        
        if 'gnome' in desktop:
            subprocess.run([
                "busctl", "--user", "call", "org.gnome.Shell", 
                "/org/gnome/Shell", "org.gnome.Shell", "Eval", "s", 
                "Main.screenShield.deactivate()"
            ], capture_output=True)
            
        elif 'kde' in desktop:
            # KDE-specifikt kommando för att väcka skärmen
            subprocess.run([
                "qdbus", "org.freedesktop.ScreenSaver", 
                "/ScreenSaver", "SimulateUserActivity"
            ], capture_output=True)

        # 3. Fallback till X11 om vi inte kör Wayland
        if os.environ.get('XDG_SESSION_TYPE') != 'wayland':
            try:
                import pyautogui
                pyautogui.press('shift')
            except: pass

def switch_input():
    global last_switch_time
    current_time = time.time()
    
    if current_time - last_switch_time < DEBOUNCE_TIME:
        return

    os_type = platform.system()
    log(f"Attempting to switch monitor input to {INPUT_CODE}...")
    
    if os_type == "Windows":
        try:
            from monitorcontrol import get_monitors
            for monitor in get_monitors():
                with monitor:
                    # newAM-biblioteket använder set_input_source
                    # INPUT_CODE kan behöva vara ett heltal, t.ex. 15 istället för "0x0f"
                    monitor.set_input_source(INPUT_CODE)
            log("Windows: Monitor input switched successfully via python library.")
        except Exception as e:
            log(f"Windows switch failed: {e}")

    else: # Linux
        try:
            # Vi behåller ddcutil på Linux då det är mer robust för system-tjänster
            subprocess.run(["ddcutil", "setvcp", "60", str(INPUT_CODE)], check=True)
            log("Linux: Monitor input switched successfully via ddcutil.")
        except Exception as e:
            log(f"Linux switch failed: {e}")

    last_switch_time = current_time

def run_listener():
    os_type = platform.system()
    log(f"KVM-daemon startad på {os_type}. Väntar på att ett tangentbord kopplas ur...")

    if os_type == "Windows":
        import wmi
        c = wmi.WMI()
        # Lyssnar efter urkopplingar av PnP-enheter
        watcher = c.watch_for(notification_type="Deletion", wmi_class="Win32_PnPEntity")
        while True:
            device = watcher()
            name = str(device.Caption) if device.Caption else ""
            # Letar efter "Keyboard" i enhetsnamnet
            if "Keyboard" in name or "Tangentbord" in name:
                log(f"Tangentbord borttaget: {name}")
                switch_input()

    elif os_type == "Linux":
        import pyudev
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        monitor.filter_by(subsystem='input')
        
        # poll() blockerar tråden effektivt utan CPU-användning
        for device in iter(monitor.poll, None):
            if device.action == 'remove':
                # Linux udev sätter ID_INPUT_KEYBOARD=1 för tangentbord
                if device.get('ID_INPUT_KEYBOARD') == '1':
                    dev_name = device.get('NAME', 'Okänt tangentbord')
                    log(f"Tangentbord borttaget: {dev_name}")
                    switch_input()

if __name__ == "__main__":
    # 1. Försök väcka datorn direkt vid start
    wake_pc()
    
    # 2. Starta lyssnaren
    try:
        run_listener()
    except KeyboardInterrupt:
        log("Daemon stoppad av användaren.")
    except Exception as e:
        log(f"Kritiskt fel i daemon: {e}")

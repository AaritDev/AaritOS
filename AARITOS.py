from logging import root
import os
import random
import sys
import time
import platform
from pathlib import Path
import shutil
from datetime import datetime
import stat
import hashlib
import getpass
import psutil

AARITOS_FOLDER = Path("aaritos")
FS_ROOT = AARITOS_FOLDER / "aaritos_fs"
CONFIG_FILE = FS_ROOT / "root" / "config.txt"
PASSWORD_FILE = FS_ROOT / "root" / "shadow"
CURRENT_USER = ""
CURRENT_DIR = FS_ROOT / "home"
IN_HOST_OS = False
HOST_ROOT = Path("C:/") if platform.system() == "Windows" else Path("/")

AARITOS_LOGO = r"""
________  ________  ________  ___  _________               ________  ________      
|\   __  \|\   __  \|\   __  \|\  \|\___   ___\            |\   __  \|\   ____\     
\ \  \|\  \ \  \|\  \ \  \|\  \ \  \|___ \  \_|____________\ \  \|\  \ \  \___|_    
 \ \   __  \ \   __  \ \   _  _\ \  \   \ \  \|\____________\ \  \\\  \ \_____  \   
  \ \  \ \  \ \  \ \  \ \  \\ \ \ \  \   \ \  \|____________|\ \  \\\  \|____|\  \  
   \ \__\ \__\ \__\ \__\ \__\\ _\\ \__\   \ \__\              \ \_______\____\_\  \ 
    \|__|\|__|\|__|\|__|\|__|\|__|\|__|    \|__|               \|_______|\_________\
"""

POWER_OFF_ART = r"""
     _____
    |     |   
    |(• •)|    POWERING OFF...
    |  ▽  |    Goodbye!
    |     |
    `‾‾‾‾‾´
"""

def get_windows_version():
    """Get the actual Windows version (10 or 11)"""
    if platform.system() != "Windows":
        return platform.system()
    
    win_version = platform.win32_ver()[0]
    build_number = int(platform.version().split('.')[2])
    
    if build_number >= 22000:
        return "Windows 11"
    else:
        return "Windows 10"

def handle_command(cmd):
    global CURRENT_DIR, IN_HOST_OS
    tokens = cmd.strip().split()
    if not tokens:
        return

    command = tokens[0]

    if command == "help":
        print("""Available commands:
    ls      - List directory contents with details
    cd      - Change directory
    pwd     - Print working directory
    mkdir   - Create directory
    rmdir   - Remove empty directory
    touch   - Create empty file
    rm      - Remove file
    cp      - Copy files
    mv      - Move files
    cat     - Display file contents
    head    - Display first lines of file
    tail    - Display last lines of file
    wc      - Count lines, words, and characters in file
    grep    - Search for a pattern in a file
    du      - Estimate file space usage
    type    - Create/edit text file
    chmod   - Change file permissions
    find    - Search for files
    tree    - Display directory structure
    date    - Show current date and time
    whoami  - Show current user
    echo    - Print text
    clear   - Clear screen
    sudo    - Execute as superuser
    neofetch- System information
    uptime  - Show system uptime
    which   - Show command location
    passwd  - Change user password (simulated)
    history - Show command history
    exit    - Exit shell
    settings- Modify shell settings
    uname   - Display system information
    ps      - Display process status
    df      - Display disk space usage
    execute - Run Windows executable (.exe) files
    kill    - Terminate a running process
    host    - Switch to host OS file browsing mode
    aaritos - Return to AaritOS filesystem from host OS
""")

    elif command == "ls":
        try:
            if IN_HOST_OS:
                for item in CURRENT_DIR.iterdir():
                    try:
                        stats = item.stat()
                        size = stats.st_size
                        mtime = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
                        file_type = "d" if item.is_dir() else "-"
                        print(f"{file_type}rw-r--r-- {size:8d} {mtime} {item.name}")
                    except Exception:
                        continue
            else:
                for item in CURRENT_DIR.iterdir():
                    stats = item.stat()
                    size = stats.st_size
                    mtime = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M")
                    file_type = "d" if item.is_dir() else "-"
                    print(f"{file_type}rw-r--r-- {size:8d} {mtime} {item.name}")
        except Exception as e:
            print(f"Error: {e}")

    elif command == "cat":
        if len(tokens) == 2:
            file_path = CURRENT_DIR / tokens[1]
            if file_path.exists():
                print(file_path.read_text())
            else:
                print("File not found")
        else:
            print("Usage: cat <filename>")

    elif command == "touch":
        if len(tokens) == 2:
            file_path = CURRENT_DIR / tokens[1]
            file_path.touch(exist_ok=True)
            print(f"Created {tokens[1]}")
        else:
            print("Usage: touch <filename>")

    elif command == "mkdir":
        if len(tokens) == 2:
            dir_path = CURRENT_DIR / tokens[1]
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Directory {tokens[1]} created")
        else:
            print("Usage: mkdir <directory>")

    elif command == "echo":
        print(" ".join(tokens[1:]))

    elif command == "whoami":
        print(CURRENT_USER)

    elif command == "type":
        if len(tokens) == 2:
            file_path = CURRENT_DIR / tokens[1]
            config = load_config()
            editor_mode = config.get("editor_mode", "vim")
            handle_type_command(file_path, editor_mode)
        else:
            print("Usage: type <filename>")

    elif command == "cd" or command == "cd..":
        if len(tokens) == 1 and command == "cd..":
            new_dir = ".."
        elif len(tokens) == 2:
            new_dir = tokens[1]
        else:
            print("Usage: cd <directory> or cd..")
            return
            
        if IN_HOST_OS:
            try:
                if new_dir == "..":
                    if CURRENT_DIR == HOST_ROOT:
                        print("Already at host root directory")
                        return
                    CURRENT_DIR = CURRENT_DIR.parent
                elif new_dir == "~":
                    CURRENT_DIR = Path.home()
                elif new_dir.startswith("/") or (platform.system() == "Windows" and ":" in new_dir):
                    new_path = Path(new_dir)
                    if new_path.exists() and new_path.is_dir():
                        CURRENT_DIR = new_path
                    else:
                        print("Directory not found")
                else:
                    new_path = CURRENT_DIR / new_dir
                    if new_path.exists() and new_path.is_dir():
                        CURRENT_DIR = new_path
                    else:
                        print("Directory not found")
            except Exception as e:
                print(f"Error: {e}")
            return

        if new_dir == "..":
            if CURRENT_DIR == FS_ROOT:
                print("Already at root directory")
                return
            CURRENT_DIR = CURRENT_DIR.parent
        elif new_dir == "~":
            CURRENT_DIR = FS_ROOT / "home" / CURRENT_USER
        elif new_dir.startswith("/"):
            dest = FS_ROOT / new_dir[1:]
            if dest.exists() and dest.is_dir():
                CURRENT_DIR = dest
            else:
                print("Directory not found")
        else:
            dest = CURRENT_DIR / new_dir
            if dest.exists() and dest.is_dir():
                CURRENT_DIR = dest
            else:
                print("Directory not found")

    elif command == "rm":
        if len(tokens) == 2:
            file_path = CURRENT_DIR / tokens[1]
            if file_path.exists():
                file_path.unlink()
                print(f"Deleted {tokens[1]}")
            else:
                print("File not found")
        else:
            print("Usage: rm <filename>")

    elif command == "clear":
        os.system("cls" if os.name == "nt" else "clear")

    elif command == "neofetch":
        print(AARITOS_LOGO)
        print(f"User: {CURRENT_USER}")
        print(f"System: AaritOS v1.0 on {get_windows_version()}")
        print(f"Shell Dir: {CURRENT_DIR}")

    elif command == "cow":
        print("""
            ^__^ 
            (oo)\_______
            (__)\       )\\/\\
                ||----w |
                ||     ||
        """)
        print("Moo. You’re doing great, Aarit.")

    elif command == "pwd":
        print(format_path_for_prompt(CURRENT_DIR))

    elif command == "sudo":
        if len(tokens) > 2 and tokens[1] == "hack" and tokens[2] == "NASA":
            print("Hacking NASA... just kidding 😂 Access denied.")
        else:
            print("Invalid sudo command")

    elif command == "cp":
        if len(tokens) == 3:
            src = CURRENT_DIR / tokens[1]
            dst = CURRENT_DIR / tokens[2]
            if src.exists():
                try:
                    shutil.copy2(src, dst)
                    print(f"Copied {tokens[1]} to {tokens[2]}")
                except Exception as e:
                    print(f"Error copying file: {e}")
            else:
                print("Source file not found")
        else:
            print("Usage: cp <source> <destination>")

    elif command == "mv":
        if len(tokens) == 3:
            src = CURRENT_DIR / tokens[1]
            dst = CURRENT_DIR / tokens[2]
            if src.exists():
                try:
                    shutil.move(src, dst)
                    print(f"Moved {tokens[1]} to {tokens[2]}")
                except Exception as e:
                    print(f"Error moving file: {e}")
            else:
                print("Source file not found")
        else:
            print("Usage: mv <source> <destination>")

    elif command == "date":
        print(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    elif command == "tree":
        def print_tree(path, prefix=""):
            try:
                for item in sorted(path.iterdir()):
                    print(f"{prefix}├── {item.name}")
                    if item.is_dir():
                        print_tree(item, prefix + "│   ")
            except Exception as e:
                print(f"Error accessing {path}: {e}")
        print_tree(CURRENT_DIR)

    elif command == "chmod":
        if len(tokens) == 3:
            try:
                mode = int(tokens[1], 8)
                path = CURRENT_DIR / tokens[2]
                if path.exists():
                    path.chmod(mode)
                    print(f"Changed permissions of {tokens[2]} to {tokens[1]}")
                else:
                    print("File not found")
            except ValueError:
                print("Invalid mode. Use octal format (e.g., 755)")
            except Exception as e:
                print(f"Error changing permissions: {e}")
        else:
            print("Usage: chmod <mode> <file>")

    elif command == "rmdir":
        if len(tokens) == 2:
            dir_path = CURRENT_DIR / tokens[1]
            if dir_path.exists() and dir_path.is_dir():
                try:
                    dir_path.rmdir()
                    print(f"Removed directory: {tokens[1]}")
                except OSError as e:
                    print(f"Error: Directory not empty or access denied - {e}")
            else:
                print("Directory not found")
        else:
            print("Usage: rmdir <directory>")

    elif command == "find":
        if len(tokens) > 1:
            pattern = tokens[1]
            def find_files(path, pattern):
                try:
                    for item in path.rglob(pattern):
                        print(item.relative_to(CURRENT_DIR))
                except Exception as e:
                    print(f"Error searching: {e}")
            find_files(CURRENT_DIR, pattern)
        else:
            print("Usage: find <pattern>")

    elif command == "head":
        if len(tokens) >= 2:
            file_path = CURRENT_DIR / tokens[1]
            lines = 10
            if len(tokens) == 4 and tokens[2] == "-n":
                try:
                    lines = int(tokens[3])
                except ValueError:
                    print("Invalid number of lines")
                    return
            if file_path.exists():
                try:
                    with file_path.open() as f:
                        for i, line in enumerate(f):
                            if i >= lines:
                                break
                            print(line.rstrip())
                except Exception as e:
                    print(f"Error reading file: {e}")
            else:
                print("File not found")
        else:
            print("Usage: head <file> [-n lines]")

    elif command == "tail":
        if len(tokens) >= 2:
            file_path = CURRENT_DIR / tokens[1]
            lines = 10
            if len(tokens) == 4 and tokens[2] == "-n":
                try:
                    lines = int(tokens[3])
                except ValueError:
                    print("Invalid number of lines")
                    return
            if file_path.exists():
                try:
                    with file_path.open() as f:
                        content = f.readlines()
                        for line in content[-lines:]:
                            print(line.rstrip())
                except Exception as e:
                    print(f"Error reading file: {e}")
            else:
                print("File not found")
        else:
            print("Usage: tail <file> [-n lines]")

    elif command == "wc":
        if len(tokens) == 2:
            file_path = CURRENT_DIR / tokens[1]
            if file_path.exists():
                try:
                    with file_path.open() as f:
                        content = f.read()
                        lines = len(content.splitlines())
                        words = len(content.split())
                        chars = len(content)
                        print(f" {lines:4d} {words:4d} {chars:4d} {file_path.name}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("File not found")
        else:
            print("Usage: wc <filename>")

    elif command == "grep":
        if len(tokens) >= 3:
            pattern = tokens[1]
            file_path = CURRENT_DIR / tokens[2]
            if file_path.exists():
                try:
                    with file_path.open() as f:
                        for i, line in enumerate(f, 1):
                            if pattern in line:
                                print(f"{i:4d}: {line.rstrip()}")
                except Exception as e:
                    print(f"Error: {e}")
            else:
                print("File not found")
        else:
            print("Usage: grep <pattern> <filename>")

    elif command == "du":
        if len(tokens) == 1:
            total = 0
            for item in CURRENT_DIR.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
            print(f"{total // 1024:4d}K\t{CURRENT_DIR.name}")
        else:
            print("Usage: du")

    elif command == "uptime":
        import time
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f" {current_time} up 0 days, 0 users, load average: 0.00, 0.00, 0.00")

    elif command == "passwd":
        if not PASSWORD_FILE.exists():
            print("No password file found.")
            return
            
        current_hash = None
        with PASSWORD_FILE.open("r") as f:
            for line in f:
                user, pwd_hash = line.strip().split(":")
                if user == CURRENT_USER:
                    current_hash = pwd_hash
                    break
        
        if not current_hash:
            print("No password set. Setting new password...")
            new_hash = get_password()
            if new_hash:
                with PASSWORD_FILE.open("a") as f:
                    f.write(f"{CURRENT_USER}:{new_hash}\n")
                print("Password set successfully!")
            return
        
        current = getpass.getpass("Current password: ")
        if not verify_password(current_hash, current):
            print("Incorrect password.")
            return
        
        print("Setting new password...")
        new_hash = get_password()
        if new_hash:
            passwords = []
            with PASSWORD_FILE.open("r") as f:
                passwords = [line.strip() for line in f]
            
            with PASSWORD_FILE.open("w") as f:
                for line in passwords:
                    user, _ = line.split(":")
                    if user == CURRENT_USER:
                        f.write(f"{CURRENT_USER}:{new_hash}\n")
                    else:
                        f.write(f"{line}\n")
            print("Password changed successfully!")

    elif command == "history":
        print("Command history:")
        print("History feature not implemented in this version")

    elif command == "which":
        if len(tokens) == 2:
            cmd = tokens[1]
            if cmd in ["ls", "cd", "pwd", "mkdir", "touch", "rm", "cp", "mv", 
                      "cat", "echo", "clear", "neofetch", "exit"]:
                print(f"/bin/{cmd}")
            else:
                print(f"Command '{cmd}' not found")
        else:
            print("Usage: which <command>")

    elif command == "settings":
        modify_settings()

    elif command == "uname":
        print(f"AaritOS v1.0 {platform.system()} {platform.machine()}")
    
    elif command == "ps":
        print("  PID TTY          TIME CMD")
        print("    1 ?        00:00:00 init")
        print(f"  {os.getpid()} pts/0    00:00:01 aaritos")
    
    elif command == "df":
        total = shutil.disk_usage("/").total // (1024 * 1024)
        used = shutil.disk_usage("/").used // (1024 * 1024)
        free = shutil.disk_usage("/").free // (1024 * 1024) 
        print("Filesystem     1M-blocks  Used Available Use%")
        print(f"aaritos          {total:9d} {used:5d}  {free:9d}  {used*100 //total}%")

    elif command == "execute":
        if len(tokens) < 2:
            print("Usage: execute <program.exe> or execute \"program name.exe\"")
            return
        
        if tokens[1].startswith('"'):
            program = ' '.join(tokens[1:])
            if program.endswith('"'):
                program = program[1:-1]
            else:
                program = program[1:]
        else:
            program = ' '.join(tokens[1:])
        
        if not program.lower().endswith('.exe'):
            program += '.exe'
        
        try:
            program_path = CURRENT_DIR / program
            if program_path.exists():
                print(f"Executing {program}...")
                os.startfile(str(program_path))
            else:
                print(f"Program not found: {program}")
        except Exception as e:
            print(f"Error executing program: {e}")

    elif command == "kill":
        if len(tokens) < 2:
            print("Usage: kill <program.exe> or kill \"program name.exe\"")
            return
        
        if tokens[1].startswith('"'):
            program = ' '.join(tokens[1:])
            if program.endswith('"'):
                program = program[1:-1]
            else:
                program = program[1:]
        else:
            program = ' '.join(tokens[1:])
        
        if not program.lower().endswith('.exe'):
            program += '.exe'
        
        try:
            found = False
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == program.lower():
                        proc.terminate()
                        found = True
                        print(f"Process {program} (PID: {proc.info['pid']}) terminated.")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            if not found:
                print(f"No running process found with name: {program}")
        except Exception as e:
            print(f"Error terminating process: {e}")

    elif command == "host":
        if IN_HOST_OS:
            print("Already in host OS mode. Use 'aaritos' to return to AaritOS.")
            return
            
        IN_HOST_OS = True
        CURRENT_DIR = HOST_ROOT
        print(f"Switched to host OS mode. Current location: {CURRENT_DIR}")
        print("Type 'aaritos' to return to AaritOS filesystem.")

    elif command == "aaritos":
        if not IN_HOST_OS:
            print("Already in AaritOS. Use 'host' to browse host OS files.")
            return
            
        IN_HOST_OS = False
        CURRENT_DIR = FS_ROOT
        print(f"Returned to AaritOS. Current location: {CURRENT_DIR}")

    else:
        print(f"Command not found: {command}")


def handle_type_command(file_path, editor_mode="vim"):
    """Enhanced type command with different editor modes"""
    print(f"Opening {file_path.name} for editing...")
    if editor_mode == "vim":
        print("VIM mode: Type ':wq' on a new line to save and exit")
        print("         Type ':q!' to exit without saving")
    else:
        print("NANO mode: Press Ctrl+X and Enter to save and exit")
        print("          Press Ctrl+C to exit without saving")
    
    lines = []
    if file_path.exists():
        lines = file_path.read_text().splitlines()
        print("\nCurrent content:")
        for i, line in enumerate(lines, 1):
            print(f"{i:3d} | {line}")
    
    print("\nEnter text (empty line to finish in nano mode):")
    try:
        while True:
            line = input()
            if editor_mode == "vim":
                if line == ":wq":
                    file_path.write_text("\n".join(lines))
                    print(f"Saved {file_path.name}")
                    break
                elif line == ":q!":
                    print("Exited without saving")
                    break
                lines.append(line)
            else:
                if not line:
                    save = input("Save changes? (y/n): ").lower()
                    if save == 'y':
                        file_path.write_text("\n".join(lines))
                        print(f"Saved {file_path.name}")
                    break
                lines.append(line)
    except KeyboardInterrupt:
        print("\nExited without saving")


def init_filesystem():
    """Initialize the AARITOS filesystem structure"""
    try:
        AARITOS_FOLDER.mkdir(parents=True, exist_ok=True)
        FS_ROOT.mkdir(parents=True, exist_ok=True)
        standard_dirs = ["root", "usr", "home", "etc", "sys", "bin", "mnt"]
        for folder in standard_dirs:
            path = FS_ROOT / folder
            path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {folder}")
        print("Filesystem initialization complete.")
    except Exception as e:
        print(f"Error initializing filesystem: {e}")
        raise

def glitch_text(text, glitch_chance=0.2):
    glitch_chars = "#$%&@!?*^~"
    return ''.join(
        c if c == '\n' or random.random() > glitch_chance else random.choice(glitch_chars)
        for c in text
    )

def animated_print(text, delay=0.02):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def boot_sequence(use_config=True):
    os.system("cls" if os.name == "nt" else "clear")
    
    for _ in range(5):
        os.system("cls" if os.name == "nt" else "clear")
        print(glitch_text(AARITOS_LOGO, glitch_chance=0.3))
        time.sleep(0.1)
    
    os.system("cls" if os.name == "nt" else "clear")
    print(AARITOS_LOGO)
    time.sleep(0.5)

    boot_lines = [
        "Booting AARITOS v1.0...",
        f"Running on: {get_windows_version()}",
        "Loading neural node drivers...",
        "Spawning virtual shell environment...",
        "Initializing system core modules...",
        "Authenticating quantum handshake...",
        "Stabilizing memory sectors...",
        "Finalizing launch sequence..."
    ]

    for line in boot_lines:
        glitched = glitch_text(line, glitch_chance=0.4)
        animated_print(glitched, delay=0.01)
        time.sleep(0.1)
    
    time.sleep(0.3)
    os.system("cls" if os.name == "nt" else "clear")
    print(AARITOS_LOGO)
    print("System boot complete.\n")
    for line in boot_lines:
        print(line)
        time.sleep(0.3)

def welcome_banner():
    print("\nEntering user-space...")
    time.sleep(0.5)
    for _ in range(3):
        sys.stdout.write(".")
        sys.stdout.flush()
        time.sleep(0.4)
    print("\n🧬 Welcome to the AARITOS shell environment 🧬\n")

def first_time_setup():
    global CURRENT_USER
    os.system("cls" if os.name == "nt" else "clear")
    print("="*60)
    print("WELCOME TO AARITOS INITIAL SETUP".center(60))
    print("="*60)
    
    CURRENT_USER = input("Enter your username: ").strip() or "aarit"
    
    print("\n=== Password Setup ===")
    password_hash = get_password()
    if password_hash:
        PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
        with PASSWORD_FILE.open("a") as f:
            f.write(f"{CURRENT_USER}:{password_hash}\n")
        print("Password set successfully!")
    
    print("\n=== Terminal Appearance ===")
    print("Choose your shell prompt color:")
    print("1) Red\n2) Green\n3) Blue\n4) Yellow\n5) Cyan\n6) Magenta\n7) Default")
    color_choice = input("Enter choice number (default 7): ").strip()
    color_map = {
        "1": "red", "2": "green", "3": "blue", 
        "4": "yellow", "5": "cyan", "6": "magenta", 
        "7": "reset"
    }
    shell_color = color_map.get(color_choice, "reset")
    
    while True:
        symbol = input("\nChoose your prompt symbol (1-4 characters, default '$'): ").strip() or "$"
        if len(symbol) <= 4:
            break
        print("Symbol must be 4 characters or less!")
    
    print("\n=== Shell Behavior ===")
    print("Choose your preferred text editor:")
    print("1) vim-style\n2) nano-style")
    editor_choice = input("Enter choice (default 2): ").strip()
    editor_mode = "vim" if editor_choice == "1" else "nano"
    
    print("\n=== Welcome Message ===")
    welcome_msg = input("Enter a custom welcome message (or leave blank for default): ").strip()
    if not welcome_msg:
        welcome_msg = "Welcome to the AARITOS shell environment 🧬"
    
    config = {
        "user": CURRENT_USER,
        "color": shell_color,
        "symbol": symbol,
        "welcome_msg": welcome_msg,
        "editor_mode": editor_mode
    }
    
    if not save_config(config):
        print("Warning: Failed to save configuration!")
        time.sleep(2)

    user_home = FS_ROOT / "home" / CURRENT_USER
    user_home.mkdir(parents=True, exist_ok=True)
    global CURRENT_DIR
    CURRENT_DIR = user_home

    print("\nSetup complete! Starting AaritOS...")
    time.sleep(2)

def load_config(skip_setup=False):
    global CURRENT_USER, CURRENT_DIR
    try:
        if CONFIG_FILE.exists():
            with CONFIG_FILE.open("r", encoding="utf-8") as f:
                config_data = f.read().strip().splitlines()
            
            config_map = {}
            for line in config_data:
                if "=" in line:
                    key, value = line.split("=", 1)
                    config_map[key] = value
            
            if config_map:
                CURRENT_USER = config_map.get("user", "aarit")
                CURRENT_DIR = FS_ROOT / "home" / CURRENT_USER
                CURRENT_DIR.mkdir(parents=True, exist_ok=True)
                return config_map
        
        if not skip_setup:
            print("No configuration found. Running first-time setup...")
            first_time_setup()
            return load_config(skip_setup=True)
        
        return {
            "user": "aarit",
            "color": "reset",
            "symbol": "$",
            "welcome_msg": "Welcome to AARITOS!",
            "editor_mode": "nano"
        }
    except Exception as e:
        if not skip_setup:
            print(f"Error loading config: {e}")
        return {
            "user": "aarit",
            "color": "reset",
            "symbol": "$",
            "welcome_msg": "Welcome to AARITOS!",
            "editor_mode": "nano"
        }

def save_config(config_map):
    """Save configuration to config file"""
    try:
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        with CONFIG_FILE.open("w", encoding="utf-8") as config:
            for key, value in config_map.items():
                config.write(f"{str(key)}={str(value)}\n")
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def modify_settings():
    """Interactive settings modification"""
    config = load_config()
    
    while True:
        print("\n=== AARITOS Settings ===")
        print("1) Change username")
        print("2) Change prompt color")
        print("3) Change prompt symbol")
        print("4) Change welcome message")
        print("5) Change text editor mode")
        print("6) Show current settings")
        print("0) Exit settings")
        
        choice = input("\nEnter choice (0-7): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            new_user = input("Enter new username: ").strip()
            if new_user:
                config["user"] = new_user
                global CURRENT_USER
                CURRENT_USER = new_user
                user_home = FS_ROOT / "home" / CURRENT_USER
                user_home.mkdir(parents=True, exist_ok=True)
        elif choice == "2":
            print("Available colors:")
            print("1) Red\n2) Green\n3) Blue\n4) Yellow\n5) Cyan\n6) Magenta\n7) Default")
            color_choice = input("Choose color (1-7): ").strip()
            color_map = {
                "1": "red", "2": "green", "3": "blue",
                "4": "yellow", "5": "cyan", "6": "magenta",
                "7": "reset"
            }
            config["color"] = color_map.get(color_choice, "reset")
        elif choice == "3":
            while True:
                new_symbol = input("Enter new prompt symbol (1-4 characters): ").strip()
                if 0 < len(new_symbol) <= 4:
                    config["symbol"] = new_symbol
                    break
                print("Symbol must be between 1 and 4 characters!")
        elif choice == "4":
            new_msg = input("Enter new welcome message: ").strip()
            if new_msg:
                config["welcome_msg"] = new_msg
        elif choice == "5":
            print("Editor modes:")
            print("1) vim-style (:wq to save)")
            print("2) nano-style (Ctrl+X to save)")
            mode = input("Choose editor mode (1-2): ").strip()
            config["editor_mode"] = "vim" if mode == "1" else "nano"
        elif choice == "6":
            print("\nCurrent settings:")
            for key, value in config.items():
                print(f"{key}: {value}")
        
        if choice in "123456":
            if save_config(config):
                print("Settings saved successfully!")
                if choice == "1":
                    global CURRENT_DIR
                    CURRENT_DIR = FS_ROOT / "home" / CURRENT_USER
            else:
                print("Failed to save settings!")

COLOR_CODES = {
    "red": "\033[91m",
    "green": "\033[92m",
    "blue": "\033[94m",
    "yellow": "\033[93m",
    "cyan": "\033[96m",
    "magenta": "\033[95m",
    "reset": "\033[0m"
}

def format_path_for_prompt(path):
    try:
        if IN_HOST_OS:
            return f"host:{path}"
            
        rel_path = path.relative_to(FS_ROOT)
        path_parts = str(rel_path).split(os.sep)
        
        if path_parts[0] == "home" and len(path_parts) > 1 and path_parts[1] == CURRENT_USER:
            if len(path_parts) == 2:
                return "~"
            return "~/" + "/".join(path_parts[2:])
        elif path_parts[0] == "home":
            return "~"
        
        return "/" + "/".join(path_parts)
    except Exception:
        return "/"

def start_shell():
    import time
    config = load_config()
    color = config.get("color", "reset")
    symbol = config.get("symbol", "$")
    welcome_msg = config.get("welcome_msg", "Welcome to the AARITOS shell environment 🧬")
    
    print(f"\n{welcome_msg}\n")
    print(f"Welcome back, {CURRENT_USER}! Type 'help' to get started.")
    while True:
        try:
            prompt_color = COLOR_CODES.get(color, COLOR_CODES["reset"])
            formatted_path = format_path_for_prompt(CURRENT_DIR)
            cmd = input(f"{prompt_color}[{CURRENT_USER}@aaritos {formatted_path}]{symbol} {COLOR_CODES['reset']}").strip()
            if cmd == "exit":
                os.system("cls" if os.name == "nt" else "clear")
                print(POWER_OFF_ART)
                print("\nShutting down AaritOS...")
                time.sleep(0.5)
                print("Saving system state...")
                time.sleep(0.5)
                print("Closing active sessions...")
                time.sleep(0.5)
                print("System halted.")
                time.sleep(1.5)
                sys.exit(0)
            else:
                handle_command(cmd)
        except (KeyboardInterrupt, EOFError):
            print("\nSession terminated. Use 'exit' next time, you chaos gremlin.")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_hash, password):
    """Verify a password against its hash"""
    return stored_hash == hash_password(password)

def get_password():
    """Get password with confirmation"""
    while True:
        password = getpass.getpass("Enter password (or press Enter to skip): ")
        if not password:
            return None
        confirm = getpass.getpass("Confirm password: ")
        if password == confirm:
            return hash_password(password)
        print("Passwords do not match. Try again.")

def login_system():
    """Handle system login with lockout"""
    if not PASSWORD_FILE.exists():
        return True

    password_hash = None
    with PASSWORD_FILE.open("r") as f:
        for line in f:
            user, pwd_hash = line.strip().split(":")
            if user == CURRENT_USER:
                password_hash = pwd_hash
                break
    
    if not password_hash:
        return True

    attempts = 0
    max_attempts = 3
    
    while attempts < max_attempts:
        try:
            password = getpass.getpass(f"Enter password for {CURRENT_USER} ({max_attempts - attempts} attempts remaining): ")
            if verify_password(password_hash, password):
                print("Login successful!")
                return True
            else:
                attempts += 1
                if attempts < max_attempts:
                    print(f"Incorrect password. {max_attempts - attempts} attempts remaining.")
                else:
                    print("Too many failed attempts. System locked.")
        except KeyboardInterrupt:
            print("\nLogin interrupted.")
            attempts += 1

    print("\nSYSTEM LOCKED")
    print("Maximum login attempts exceeded. System permanently locked.")
    print("Please contact system administrator.")
    return False

if __name__ == "__main__":
    try:
        print("Initializing filesystem...")
        AARITOS_FOLDER.mkdir(parents=True, exist_ok=True)
        FS_ROOT.mkdir(parents=True, exist_ok=True)
        init_filesystem()

        print("\nStarting AaritOS...")
        boot_sequence(use_config=False)
        
        config_exists = CONFIG_FILE.exists() and CONFIG_FILE.stat().st_size > 0
        
        if config_exists:
            try:
                config = load_config(skip_setup=True)
                if not config or not any(key in config for key in ["user", "color", "symbol"]):
                    raise ValueError("Invalid config format")
                
                if not login_system():
                    print("\nAccess denied. System locked.")
                    sys.exit(1)
                
                welcome_banner()
                start_shell()
            except Exception as e:
                print(f"Configuration corrupted: {e}")
                print("Running first-time setup...")
                first_time_setup()
                
                if not login_system():
                    print("\nAccess denied. System locked.")
                    sys.exit(1)
                    
                welcome_banner()
                start_shell()
        else:
            print("\nNo configuration found.")
            print("Running first-time setup...")
            first_time_setup()
            
            if not login_system():
                print("\nAccess denied. System locked.")
                sys.exit(1)
                
            welcome_banner()
            start_shell()
        
    except Exception as e:
        print(f"Critical error: {e}")
        input("Press Enter to exit...")

import os
from proxy_detector import is_running_on_macos
from settings import MySetts


def print_environment_info():
    """Print information about the current environment and settings"""
    print("===== Environment Information ======")
    print(f"Running on macOS: {is_running_on_macos()}")
    print(f"Use proxy: {MySetts.use_proxy}")
    print(f"AI provider: {MySetts.ai_provider}")
    if MySetts.use_proxy:
        print(f"HTTP proxy: {MySetts.yf_proxy}")
        print(f"HTTPS proxy: {MySetts.yfs_proxy}")
        print(f"SOCKS proxy: {MySetts.yf_socks_proxy}")
    
    # Print system information
    import platform
    print(f"\nSystem information:")
    print(f"OS name: {platform.system()}")
    print(f"OS version: {platform.version()}")
    print(f"Machine: {platform.machine()}")
    print(f"Platform: {platform.platform()}")
    print("===================================")


if __name__ == "__main__":
    print_environment_info()
import urllib.request
import platform

def is_running_on_macos():
    """Check if the operating system is macOS"""
    try:
        # Get the current OS name
        os_name = platform.system().lower()
        # Check if it contains 'darwin' (macOS internal name)
        return 'darwin' in os_name
    except:
        return False


def detect_system_proxy():
    """Detect system proxy settings"""
    try:
        # Get system proxy settings from urllib
        proxies = urllib.request.getproxies()
        #print(proxies,not proxies)
        # Check for http proxy
        if 'http' in proxies:
            return proxies['http']
        # Check for https proxy
        elif 'https' in proxies:
            return proxies['https']
        # Check for all_proxy
        elif 'all_proxy' in proxies:
            return proxies['all_proxy']
        # Check for ALL_PROXY
        elif 'ALL_PROXY' in proxies:
            return proxies['ALL_PROXY']
        return None
    except Exception as e:
        print(proxies,e)
        return None




# proxies = urllib.request.getproxies()
# use_proxy = True if proxies else False
# yf_proxy = proxies.get('http', None)
# yfs_proxy = proxies.get('https', yf_proxy)
# yf_socks_proxy = proxies.get('socks', None)
# print(use_proxy,yf_proxy,yfs_proxy,yf_socks_proxy)
# return proxies


if __name__ == "__main__":
    proxy1 = detect_system_proxy()
    print(1, proxy1)
    is_macos = is_running_on_macos()
    print(2, is_macos)

import os
import urllib.request

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


def another_approach():
    print("another_approach")
    
    """Another approach to detect system proxy settings"""
    try:
        # Get system proxy settings from environment variables
        http_proxy = os.environ.get('http_proxy')
        https_proxy = os.environ.get('https_proxy')
        all_proxy = os.environ.get('all_proxy')
        ALL_PROXY = os.environ.get('ALL_PROXY')

        # Check for http proxy
        if http_proxy:
            return http_proxy
        # Check for https proxy
        elif https_proxy:
            return https_proxy
        # Check for all_proxy
        elif all_proxy:
            return all_proxy
        # Check for ALL_PROXY
        elif ALL_PROXY:
            return ALL_PROXY
        return None
    except Exception as e:
        print(e)
        return None

def third_approach():
    proxies = urllib.request.getproxies()
    use_proxy = True if proxies else False
    yf_proxy = proxies.get('http', None)
    yfs_proxy = proxies.get('https', yf_proxy)
    yf_socks_proxy = proxies.get('socks', None)
    print(use_proxy,yf_proxy,yfs_proxy,yf_socks_proxy)
    return proxies


if __name__ == "__main__":
    proxy1 = detect_system_proxy()
    print(1, proxy1)
    proxy2 = another_approach()
    print(2, proxy2)
    proxy3 = third_approach()
    print(3, proxy3)

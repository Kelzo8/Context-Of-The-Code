import socket

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        # Create a socket that connects to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # It doesn't actually connect
        s.connect(("8.8.8.8", 80))
        # Get the local IP address
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Error getting local IP: {e}")
        return "Could not determine local IP"

if __name__ == "__main__":
    local_ip = get_local_ip()
    print("\nYour local IP address is:")
    print(f"  {local_ip}")
    print("\nYour API will be available at:")
    print(f"  http://{local_ip}:5000")
    print("\nUse this URL for the API_URL environment variable in PythonAnywhere")
    print(f"  http://{local_ip}:5000")
    print("\nNote: This IP address may change if you restart your computer or reconnect to the network.") 
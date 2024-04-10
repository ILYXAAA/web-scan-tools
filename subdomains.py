import requests

def get_subdomains(domain):
    api_key = "wW74jcuFzZgN9oAtljoZYiiIXsd2Fif9"  # замените на ваш API ключ от SecurityTrails
    url = f"https://api.securitytrails.com/v1/domain/{domain}/subdomains?children_only=false&include_inactive=true"

    headers = {
        "APIKEY": api_key
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            subdomains = data.get("subdomains", [])
            print(f"Number of subdomains: {len(subdomains)}")
            with open(f"Results/{domain}_result.txt", "w") as file:
                for subdomain in subdomains:
                    file.write(f"http://{subdomain}.{domain}" + "\n")
            return subdomains
        else:
            print(f"{response=}")
            print(f"{response.content=}")
            print(f"Failed to retrieve subdomains. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []
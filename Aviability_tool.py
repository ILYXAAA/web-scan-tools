import concurrent.futures
import requests
import os
from tqdm import tqdm
from subdomains import get_subdomains

def check_website(url):
    try:
        response = requests.get(url, timeout=10, stream=True)
        if response.status_code == 200:
            return url
    except Exception as e:
        pass
    return None

def main():
    your_sites = input("Enter domains (delimeter - ;): ").split(";")#"lk.npfsb.ru" 
    for your_site in your_sites:
        input_file = f"Results/{your_site}_result.txt"  # Путь к файлу с сайтами
        output_file = f"Avaible/{your_site}_available_sites.txt"  # Путь к файлу для записи доступных сайтов
        if os.path.exists(input_file):
            sub_domains = True
        else:
            sub_domains = get_subdomains(your_site)
        
        if sub_domains:
            with open(input_file, "r") as file:
                sites = file.readlines()
            sites = [site.strip() for site in sites]

            available_sites = []

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(check_website, sites)
                total_sites = len(sites)

                with tqdm(total=total_sites, desc="Checking websites") as pbar:
                    for result in results:
                        if result:
                            available_sites.append(result)
                        pbar.update(1)

            with open(output_file, "w") as file:
                file.write("http://" + your_site + "\n")
                for site in available_sites:
                    file.write(site + "\n")

            print("Done. Available sites saved in:", output_file)

if __name__ == "__main__":
    main()
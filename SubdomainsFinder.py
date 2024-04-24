import requests
import concurrent.futures
import requests
import os
from tqdm import tqdm
from fake_useragent import UserAgent
import urllib3
from datetime import datetime
import json
import argparse

class SubdomainsFinder:
    def __init__(self, site:str = None, securitytrails_api_key:str = None, output_folder:str = "Results/SubdomainsFinder_RawResults") -> None:
        self.SEC_TRAILS_API_KEY = securitytrails_api_key
        self.OUTPUT_FOLDER = output_folder
        
        if site:
            self.your_site = site
        else:
            self.your_site = input("Enter domain: ")

    @staticmethod
    def check_website(url):
        try:
            ua = UserAgent()
            headers = {'User-Agent': ua.random}
            response = requests.get(url=url, headers=headers, timeout=10, stream=True)

            if str(response.status_code)[0] == "2":
                return (True, response.status_code, "Success", url)
            elif str(response.status_code)[0] == "3":
                return (False, response.status_code, "Redirection", url)
            elif response.status_code == 400:
                return (False, response.status_code, "Bad Request", url)
            elif response.status_code == 401:
                return (False, response.status_code, "Unauthorized", url)
            elif response.status_code == 402:
                return (False, response.status_code, "Payment Required", url)
            elif response.status_code == 403:
                return (False, response.status_code, "Forbidden", url)
            elif response.status_code == 403:
                return (False, response.status_code, "Forbidden", url)
            elif response.status_code == 404:
                return (False, response.status_code, "Not Found", url)
            elif response.status_code == 405:
                return (False, response.status_code, "Method Not Allowed", url)
            elif response.status_code == 408:
                return (False, response.status_code, "Request Timeout", url)
            elif response.status_code == 429:
                return (False, response.status_code, "Too Many Requests", url)
            elif str(response.status_code)[0] == "5":
                return (False, response.status_code, "Server error", url)
        
        except requests.exceptions.ConnectionError:
            return (False, None, "requests.exceptions.Connectionrrror", url)
        except urllib3.exceptions.MaxRetryError:
            return (False, None, "urllib3.exceptions.MaxRetryError", url)
        except requests.exceptions.ReadTimeout:
            return (False, None, "requests.exceptions.readTimeout", url)
        except Exception:
            return (False, None, "Some another Error", url)
        return (False, response.status_code, "Status not assigned", url)

    def get_subdomains(self, domain):
        if not self.SEC_TRAILS_API_KEY:
            print(f"[LOG] <<KEY IS REQUIRED>> SecurityTrails API KEY is required\n")
            while not self.SEC_TRAILS_API_KEY:
                self.SEC_TRAILS_API_KEY = input(f"Enter SecurityTrails API KEY: \n>")
            
        url = f"https://api.securitytrails.com/v1/domain/{domain}/subdomains?children_only=false&include_inactive=true"

        headers = {
            "accept": "application/json",
            "APIKEY": self.SEC_TRAILS_API_KEY
        }

        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                subdomains = data.get("subdomains", [])
                print(f"[LOG] <<INFO>> Found [{len(subdomains)}] subdomains for - '{domain}'")
                with open(f"{self.OUTPUT_FOLDER}/{domain}_Raw_Result.txt", "w") as file:
                    file.write("\n".join(f"http://{sub}.{domain}" for sub in subdomains))

                print(f"[LOG] <<SAVING>> Raw results saved in: {self.OUTPUT_FOLDER}/{domain}_Raw_Result.txt\n")
                return subdomains
            else:
                print(f"[LOG] <<StatusCode ERROR>> {response=}")
                print(f"[LOG] <<StatusCode ERROR>> {response.content=}")
                print(f"[LOG] <<StatusCode ERROR>> Failed to retrieve subdomains. Status code: {response.status_code}\n")
                return []
        except Exception as e:
            print(f"[LOG] An error occurred: {e}\n")
            return []
    
    def start_aviability_scanner(self):
        if not os.path.exists("Results/SubdomainsFinder_RawResults"):
            os.mkdir("Results/SubdomainsFinder_RawResults")
        if not os.path.exists("Results/SubdomainsFinder_FinalResults"):
            os.mkdir("Results/SubdomainsFinder_FinalResults")
        if not os.path.exists("last_launch.log"):
            with open("last_launch.log", "w") as file:
                file.write("")
        with open("last_launch.log", "a") as file:
            formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"\n[{formatted_time}] SubdomainsFinder Started..\n")

        total_errors_count = 0
        total_found = 0

        input_file = f"Results/SubdomainsFinder_RawResults/{self.your_site}_Raw_Result.txt"  # Путь к файлу с поддоменами сайта
        output_file = f"Results/SubdomainsFinder_FinalResults/{self.your_site}_AvaibleSubdomains.txt"  # Путь к файлу для записи доступных поддоменов
        if os.path.exists(input_file):
            sub_domains = True
        else:
            sub_domains = self.get_subdomains(self.your_site)
        
        if sub_domains:
            with open(input_file, "r") as file:
                sites = file.readlines()
            sites = [site.strip() for site in sites]

            available_sites = []

            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(self.check_website, sites)
                total_sites = len(sites)

                with tqdm(total=total_sites, desc="Checking subdomens status") as pbar:
                    for result in results:
                        status, status_code, description, url = result[0], result[1], result[2], result[3]
                        with open("last_launch.log", "a") as file:
                            file.write(f"[{status_code}] - <<{description}>> - {url}\n")

                        pbar.set_postfix_str(url)
                        if "Error" in description:
                            total_errors_count += 1
                        if status:
                            total_found += 1
                            available_sites.append(url)
                        pbar.set_description(f"Checking Raw Subdomains. Errors: {total_errors_count}; Found: {total_found}") 
                        pbar.update(1)

            with open(output_file, "w") as file:
                file.write("http://" + self.your_site + "\n")
                file.write("\n".join(available_sites))

            print(f"[LOG] <<SAVING>> {len(available_sites)} of subdomains are avaible.\n[LOG] Results saved in: '{output_file}'\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Поиск под-доменов сайта')
    parser.add_argument('-u', '--url', type=str, default=None, help='Ссылка на сайт')
    parser.add_argument('-t', '--token', type=str, default=None, help='API Токен сайта SecurityTrails')
    args = parser.parse_args()
    domain = args.url
    token = args.url
    if not domain:
        input(f"Enter domain for scan:\n>").replace("https://", "").replace("http://", "")
    if not token:     
        try:
            with open(f"config.json", "r") as file:
                CONFIG = json.loads(file.read())
            token = CONFIG["SecurityTrails_API_TOKEN"]
        except Exception as error:
            token = input("Enter your SecurityTrails API Token: ")

    Finder = SubdomainsFinder(site=domain, securitytrails_api_key=token)
    Finder.start_aviability_scanner()
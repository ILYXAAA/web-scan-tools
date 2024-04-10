import concurrent.futures
import requests
import os
from tqdm import tqdm
import signal
from fake_useragent import UserAgent
import os
import time
from datetime import datetime
import urllib3

class DirPathFinder:
    def __init__(self, proxy_list_file="Dictionary/proxy_list.txt", your_site=None, paths_dictionary="Dictionary/dict_1000_dirs.txt", exclude_flag_phrase=None) -> None:
        if not os.path.exists("Results/DirpathFinder_Results"):
            os.mkdir("Results/DirpathFinder_Results")
        if not os.path.exists("Results/TMP_DirpathFinder_Results"):
            os.mkdir("Results/TMP_DirpathFinder_Results")

        self.proxy_list_file = proxy_list_file
        self.your_site = your_site
        self.exclude_flag_phrase = exclude_flag_phrase
        if not self.your_site:
            while not self.your_site:
                self.your_site = input(f"[LOG] <<DATA REQUIRED>> Enter domain:\n>")
        self.paths_dictionary = paths_dictionary  # Путь к файлу с словарём paths        
        self.output_file = f"Results/DirpathFinder_Results/{self.your_site}_AvailablePaths.txt"  # Путь к файлу для записи доступных сайтов

        #Proxy func in progress..
        self.proxies = None
        self.use_proxy=False
        if self.use_proxy:
            if self.is_file_created_more_than_day_ago(self.proxy_list_file):
                print(f"[LOG] Your '{self.proxy_list_file}' needs update..")
                with open("last_launch.log", "a") as file:
                    file.write(f"[LOG] - Your '{self.proxy_list_file}' needs update..")
                try:
                    response = requests.get("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt")
                    with open(f"Dictionary/proxy_list.txt", "w") as file:
                        file.write(response.content.decode())
                    print(f"[LOG] Your {self.proxy_list_file} sucessfully updated")
                except Exception as error:
                    print(f"[LOG] Error with updating '{self.proxy_list_file}'")
                    with open("last_launch.log", "a") as file:
                        file.write(f"[LOG] - Error with updating '{self.proxy_list_file}'")
                    print(error)

            if os.path.exists("Dictionary/proxy_list.txt"):
                with open("Dictionary/proxy_list.txt", "r") as file:
                    self.proxies = file.readlines()
                self.proxies = [proxy.strip() for proxy in self.proxies]
            else:
                self.proxies = None
        #Proxy func in progress..

    @staticmethod
    def is_file_created_more_than_day_ago(file_path):
        if not os.path.exists(file_path):
            return True
        created_time = os.path.getctime(file_path)
        current_time = time.time()
        time_difference = current_time - created_time
        if time_difference > 86400:
            return True
        else:
            return False
    
    @staticmethod
    def check_website(url):
        try:
            ua = UserAgent()
            headers = {'User-Agent': ua.random}
            response = requests.get(url=url, headers=headers, timeout=10, stream=True)

            if str(response.status_code)[0] == "2":
                return (True, response.status_code, "Success", url, response.content.decode())
            elif str(response.status_code)[0] == "3":
                return (False, response.status_code, "Redirection", url, response.content.decode())
            elif response.status_code == 400:
                return (False, response.status_code, "Bad Request", url, response.content.decode('utf-8'))
            elif response.status_code == 401:
                return (False, response.status_code, "Unauthorized", url, response.content.decode('utf-8'))
            elif response.status_code == 402:
                return (False, response.status_code, "Payment Required", url, response.content.decode('utf-8'))
            elif response.status_code == 403:
                return (False, response.status_code, "Forbidden", url, response.content.decode('utf-8'))
            elif response.status_code == 403:
                return (False, response.status_code, "Forbidden", url, response.content.decode('utf-8'))
            elif response.status_code == 404:
                return (False, response.status_code, "Not Found", url, response.content.decode('utf-8'))
            elif response.status_code == 405:
                return (False, response.status_code, "Method Not Allowed", url, response.content.decode('utf-8'))
            elif response.status_code == 408:
                return (False, response.status_code, "Request Timeout", url, response.content.decode('utf-8'))
            elif response.status_code == 429:
                return (False, response.status_code, "Too Many Requests", url, response.content.decode('utf-8'))
            elif str(response.status_code)[0] == "5":
                return (False, response.status_code, "Server error", url, response.content.decode('utf-8'))
        
        except requests.exceptions.ConnectionError:
            return (False, None, "requests.exceptions.ConnectionError", url, "")
        except urllib3.exceptions.MaxRetryError:
            return (False, None, "urllib3.exceptions.MaxRetryError", url, "")
        except requests.exceptions.ReadTimeout:
            return (False, None, "requests.exceptions.ReadTimeout", url, "")
        except Exception as error:
            return (False, None, str(error), url, "")
        return (False, response.status_code, "Status not assigned", url, response.content.decode())

    def start_dir_scanner(self):    
        total_errors_count = 0
        total_found = 0
        
        with open(self.paths_dictionary, "r") as file:
            paths_prefixs = file.readlines()
        paths_prefixs = [f"http://{self.your_site}/{path.strip()}" for path in paths_prefixs]
        available_sites = []

        if not os.path.exists("last_launch.log"):
            with open("last_launch.log", "w") as file:
                file.write("")
        with open("last_launch.log", "a") as file:
            formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"\n[{formatted_time}] DirpathFinder Started..\n")

        def handle_sigint(signum, frame):
            print("\n[LOG] Received SIGINT, terminating...")
            tmp_output_file = self.output_file.replace(self.your_site, f"tmp_{self.your_site}").replace("Results/DirpathFinder_Results/", "Results/TMP_DirpathFinder_Results/")
            with open("last_launch.log", "a") as file:
                file.write(f"[Ctrl+C 'Error'] <<CTRL+C Detected>> - Temporary result saved to '{tmp_output_file}'\n")
            self.write_results_to_file(available_sites, tmp_output_file)
            os._exit(1)

        signal.signal(signal.SIGINT, handle_sigint)

        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                results = executor.map(self.check_website, paths_prefixs)
                total_sites = len(paths_prefixs)

                with tqdm(total=total_sites, desc="Checking dirs in domain") as pbar:
                    for result in results:
                        status, status_code, description, url, page_content = result[0], result[1], result[2], result[3], result[4]
                        if self.exclude_flag_phrase:
                            if self.exclude_flag_phrase in page_content:
                                status = False
                                description = f"Exclude phrase found: '{self.exclude_flag_phrase}'"
                                status_code = f"{str(status_code)}:False"
                        
                        with open("last_launch.log", "a") as file:
                            file.write(f"[{status_code}] - <<{description}>> - {url}\n")
                        
                        if "Error" in description:
                            total_errors_count += 1
                        pbar.set_postfix_str(f"{url}")
                    
                        if status:
                            available_sites.append(url)
                            total_found += 1
                        
                        pbar.set_description(f"Checking status. Errors: {total_errors_count}; Found: {total_found}") 
                        pbar.update(1)
                        #print(available_sites)
            self.write_results_to_file(available_sites, self.output_file)
        
        except KeyboardInterrupt:
            print("\n[LOG] KeyboardInterrupt received, terminating...")
            with open("last_launch.log", "a") as file:
                file.write("[LOG] - KeyboardInterrupt received, terminating...\n")
            self.write_results_to_file(available_sites, self.output_file)

    @staticmethod
    def write_results_to_file(results, output_file):
        if results:
            with open(output_file, "w") as file:
                file.write("\n".join(results))
            print("[LOG] Results written to:", output_file)
            with open("last_launch.log", "a") as file:
                file.write(f"[LOG] - Results written to: '{output_file}'\n")
        else:
            print("[LOG] No results to write.")
            with open("last_launch.log", "a") as file:
                file.write(f"[LOG] - No results to write.\n")

if __name__ == "__main__":
    domain = input(f"Enter domain for scan:\n>").replace("https://", "").replace("http://", "")
    Finder = DirPathFinder(your_site=domain, paths_dictionary="Dictionary/dict_1000_dirs.txt")
    Finder.start_dir_scanner()
import concurrent.futures
import requests
import os
from tqdm import tqdm
import signal
from fake_useragent import UserAgent
import random
import os
import time
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
    
def check_website(url):
    try:
        ua = UserAgent()
        headers = {'User-Agent': ua.random}
        response = requests.get(url=url, headers=headers, timeout=10, stream=True)

        if str(response.status_code)[0] == "2":
            return (True, response.status_code, "Success", url)
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
        elif str(response.status_code)[0] == "3":
            return (False, response.status_code, "Redirection", url)
        elif str(response.status_code)[0] == "5":
            return (False, response.status_code, "Server Error", url)
        
    except Exception as e:
        #print(e)
        write_error_to_log(url, e)
        return (False, None, "Error", url)
    return (False, response.status_code, "Status not assigned", url)

def write_error_to_log(url, error):
    with open("last_launch.log", "a") as file:
        file.write(f"[{url}]\n{error}\n\n")

def main():
    proxy_list_file = "Dictionary/proxy_list.txt"
    your_site = input("Enter domain: ") #"lk.npfsb.ru" 
    paths_dictionary = f"Dictionary/dict_1000_dirs.txt"  # Путь к файлу с сайтами
    output_file = f"Avaible_paths/{your_site}_available_paths.txt"  # Путь к файлу для записи доступных сайтов
    total_errors_count = 0
    total_found = 0
    
    #Proxy func in progress..
    proxies = None
    use_proxy=False
    if use_proxy:
        if is_file_created_more_than_day_ago(proxy_list_file):
            print(f"[LOG] Your {proxy_list_file} needs update..")
            try:
                response = requests.get("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt")
                with open(f"Dictionary/proxy_list.txt", "w") as file:
                    file.write(response.content.decode())
                print(f"[LOG] Your {proxy_list_file} sucessfully updated")
            except Exception as error:
                print(f"[LOG] Error with updating {proxy_list_file}")
                print(error)

        if os.path.exists("Dictionary/proxy_list.txt"):
            with open("Dictionary/proxy_list.txt", "r") as file:
                proxies = file.readlines()
            proxies = [proxy.strip() for proxy in proxies]
        else:
            proxies = None

    with open(paths_dictionary, "r") as file:
        paths_prefixs = file.readlines()
    paths_prefixs = [f"http://{your_site}/{path.strip()}" for path in paths_prefixs]
    available_sites = []

    with open("log.txt", "w") as file:
        file.write("")

    def handle_sigint(signum, frame):
        print("\n[LOG] Received SIGINT, terminating...")
        write_results_to_file(available_sites, output_file.replace(your_site, f"tmp_{your_site}"))
        os._exit(1)

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            results = executor.map(check_website, paths_prefixs)
            total_sites = len(paths_prefixs)

            with tqdm(total=total_sites, desc="Checking websites") as pbar:
                for result in results:
                    status, status_code, description, url = result[0], result[1], result[2], result[3]
                    with open("log.txt", "a") as file:
                        file.write(f"[{status_code}] - <<{description}>> - {url}\n")
                    
                    if description == "Error":
                        total_errors_count += 1
                    pbar.set_postfix_str(f"{url}")
                
                    if status:
                        available_sites.append(url)
                        total_found += 1
                    
                    pbar.set_description(f"Use_Proxy: {use_proxy}; Errors: {total_errors_count}; Found: {total_found}") 
                    pbar.update(1)
                    #print(available_sites)
        write_results_to_file(available_sites, output_file)
    
    except KeyboardInterrupt:
        print("\n[LOG] KeyboardInterrupt received, terminating...")
        write_results_to_file(available_sites, output_file)

def write_results_to_file(results, output_file):
        if results:
            with open(output_file, "w") as file:
                for site in results:
                    file.write(site + "\n")
            print("[LOG] Results written to:", output_file)
        else:
            print("[LOG] No results to write.")

if __name__ == "__main__":
    main()

import requests
import os
from tqdm import tqdm
import signal
from fake_useragent import UserAgent
import os
import time
from datetime import datetime
import urllib3
import re
import pickle
import argparse
import threading
from Colors import Colors
import concurrent.futures
import urllib.request

class DirPathFinder:
    def __init__(self, proxy_list_file="Dictionary/proxy_list.txt", your_site=None, paths_dictionary="Dictionary/dict_4600_dirs.txt", exclude_flag_phrase=None, seconds_parameter=30, max_errors_number=30, seconds_to_sleep=30, max_threads_number=10, use_proxy=False, skip_errors_flag=True) -> None:
        # Создание директорий программы (если их нет)
        if not os.path.exists("Results"):
            os.mkdir("Results")
        if not os.path.exists("Progress"):
            os.mkdir("Progress")
        if not os.path.exists("Results/DirpathFinder_Results"):
            os.mkdir("Results/DirpathFinder_Results")
        if not os.path.exists("Results/TMP_DirpathFinder_Results"):
            os.mkdir("Results/TMP_DirpathFinder_Results")
        if not os.path.exists("last_launch.log"):
            with open("last_launch.log", "w") as file:
                file.write("")
        with open("last_launch.log", "a") as file:
            formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            file.write(f"\n[{formatted_time}] DirpathFinder Started..\n")
        
        #Удаляем все ненужные TMP файлы
        self.keep_highest_percentage_files()

        # Фраза, если встречается на сайте, то status != 200
        self.exclude_flag_phrase = exclude_flag_phrase 
        
        # Требуем ввместе домен для сканирования
        self.your_site = your_site
        if not self.your_site:
            while not self.your_site:
                self.your_site = input(f"{Colors.YELLOW}[LOG] <<DATA REQUIRED>>{Colors.END} Enter domain:\n[INPUT] >")

        self.skip_errors_flag = skip_errors_flag # Не перепроверять сайты, свалившиеся с ошибкой
        
        self.current_iteration = None # Для progress pickle
        self.current_percentage = None # Для `красивого` названия TMP файлов
        self.current_total_iterations = None # Для `красивого` названия TMP файлов

        self.executor = None # Основной executor потоков
        self.max_threads_number = max_threads_number # Максимальное количество потоков

        self.seconds_parameter = seconds_parameter # для check_errors: Время -> за которые считаются ошибки (сек)
        self.max_errors_number = max_errors_number # для check_errors: Количество -> ошибок за это время, чтобы сработал сон
        self.seconds_to_sleep = seconds_to_sleep # для check_errors: Время -> на которое засыпают все потоки (сек) 
        self.errors_dict = {} # для check_errors: Словарь -> в который логируются все ошибки с таймлайнами
        
        self.output_file = f"Results/DirpathFinder_Results/{self.your_site}_AvailablePaths.txt"  # Путь к файлу для записи доступных сайтов
        self.paths_dictionary = paths_dictionary  # Путь к файлу с словарём paths
        
        print(f"{Colors.BLUE}[LOG] <<INFO>>{Colors.END} Program launched with {self.max_threads_number} threads")
        time.sleep(0.05)
        print(f"{Colors.BLUE}[LOG] <<INFO>>{Colors.END} Domain for scan: '{self.your_site}'")
        time.sleep(0.05)
        print(f"{Colors.BLUE}[LOG] <<INFO>>{Colors.END} Dictionary: '{self.paths_dictionary}'")
        time.sleep(0.05)

        # Proxy functinal
        self.proxy_list_file = proxy_list_file
        self.proxies = None
        self.use_proxy=use_proxy
        self.valid_proxy = None

        if self.use_proxy:
            if self.is_file_created_more_than_3h_ago(self.proxy_list_file):
                print(f"{Colors.YELLOW}[LOG] <<UPDATE>>{Colors.END} - Your '{self.proxy_list_file}' needs update..")
                time.sleep(0.05)
                with open("last_launch.log", "a") as file:
                    file.write(f"[LOG] - Your '{self.proxy_list_file.replace('Dictionary/', '')}' needs update..")
                
                file_size = 0
                try:
                    d = urllib.request.urlopen("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt")
                    file_size = int(d.info()["Content-Length"])/1024
                except Exception as error:
                    print(f"{Colors.RED}[LOG] <<Error>>{Colors.END} - Error with counting file size for 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt'")
                    time.sleep(0.05)
                    with open("last_launch.log", "a") as file:
                        file.write(f"[LOG] <<Error>> - Error with counting file size for 'https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt'")

                answer = input(f"{Colors.YELLOW}[LOG] <<UPDATE>>{Colors.END} - Do you want to update '{self.proxy_list_file}' [Size: {round(file_size, 1)} KB]?\n[INPUT] >")
                if "y" in answer.lower():
                    try:
                        response = requests.get("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/http.txt")
                        with open(self.proxy_list_file, "w") as file:
                            file.write(response.content.decode())
                        print(f"{Colors.GREEN}[LOG] <<SUCCESS>>{Colors.END} - Your {self.proxy_list_file} sucessfully updated")
                        time.sleep(0.05)
                    except Exception as error:
                        print(f"{Colors.RED}[LOG] <<Error>>{Colors.END} - Error with updating '{self.proxy_list_file}'")
                        time.sleep(0.05)
                        with open("last_launch.log", "a") as file:
                            file.write(f"[LOG] <<Error>> - Error with updating '{self.proxy_list_file}'")
                        print(error)

            if os.path.exists(self.proxy_list_file):
                with open(self.proxy_list_file, "r") as file:
                    self.proxies = file.readlines()
                self.proxies = [proxy.strip() for proxy in self.proxies]
            else:
                self.proxies = None
                self.use_proxy = False

        # Проверка есть ли сохраненный прошлый прогресс
        self.available_sites = []
        self.total_found = 0
        self.total_errors_count = 0
        self.current_iteration = 0
        self.current_percentage = 0
        progress_file = None
        progress_files = os.listdir("Progress")
        for file in progress_files:
            try:
                if self.your_site == file.split("_")[0] and paths_dictionary.replace('Dictionary/', '').replace('.txt', '') in file:
                    progress_file = "Progress/" + file
                    break
            except IndexError:
                pass
        if progress_file:
            self.current_iteration, self.available_sites, self.total_errors_count, self.total_found = self.load_progress(progress_file=progress_file)            

    def check_proxy(self, proxy):
        try:
            response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
            if response.status_code == 200:
                return proxy  # Если прокси валиден, возвращаем его
            else:
                return None
        except Exception as e:
            return None
        
    def find_valid_proxy(self, filename, batch_size=10):
        try:
            with open(f"Dictionary/{filename}", 'r') as file:
                proxies = file.readlines()

            total_proxies = len(proxies)
            current_iter = 0
            num_batches = (total_proxies + batch_size - 1) // batch_size

            for i in range(num_batches):
                batch = proxies[i * batch_size: (i + 1) * batch_size]
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    results = executor.map(self.check_proxy, batch)
                    for result in results:
                        current_iter += 1
                        if result is not None:
                            self.valid_proxy = result  # Сохраняем найденный валидный прокси
                            executor.shutdown(wait=True)  # Останавливаем все потоки
                            return  # Завершаем поиск после первого найденного валидного прокси
                tqdm.write(f"{Colors.BLUE}[LOG] <<INFO>>{Colors.END} - Searching valid proxy... {current_iter}/{total_proxies}")
            self.valid_proxy = None
        except Exception as error:
            self.valid_proxy = None  
            print(f"\n{Colors.RED}[LOG] <<ERROR>>{Colors.END} - Some error in `find_valid_proxy`: {error}")
            time.sleep(0.05)

    def check_errors(self):
        try:
            # Удаляем времена ошибок, которые были более seconds_parameter секунд назад
            current_time = time.time()
            self.errors_dict = {key: value for key, value in self.errors_dict.items() if current_time - value <= self.seconds_parameter}

            # Проверяем количество ошибок
            if len(self.errors_dict) >= self.max_errors_number:
                # Вычисляем разницу в секундах между первой и последней ошибками
                time_difference = int(max(self.errors_dict.values()) - min(self.errors_dict.values()))
                returnstring = f"{Colors.RED}[LOG] <<ERRORS>>{Colors.END} - Too many errors... ({self.max_errors_number} errors in {time_difference} seconds)"
                self.errors_dict.clear()  # Очищаем словарь ошибок
                if not self.skip_errors_flag:
                    self.current_iteration = self.current_iteration - self.max_errors_number
                    self.total_errors_count = self.total_errors_count - self.max_errors_number
                return False, returnstring
            else:
                return True, None
        except Exception as error:
            returnstring = f"{Colors.RED}[LOG] <<ERROR>>{Colors.END} - Some error in `check_errors`: {error}"   
            return True, returnstring
        
    def save_progress(self, progress_file, iteration, avaible_sites, total_errors_count, total_found):
        try:
            with open(progress_file, "wb") as f:
                pickle.dump((iteration, avaible_sites, total_errors_count, total_found), f)
                with open("last_launch.log", "a") as file:
                    file.write(f"[LOG] <<SAVE>> - progress saved to {progress_file}\n")
                print(f"{Colors.GREEN}[LOG] <<SAVE>>{Colors.END} - progress saved to {progress_file}")
                time.sleep(0.05)
                print(f"{Colors.BLUE}[LOG] <<SAVED VARS>>:{Colors.END}")
                time.sleep(0.05)
                print(f"{Colors.BLUE}   - {iteration=}{Colors.END};")
                time.sleep(0.05)
                print(f"{Colors.BLUE}   - {total_errors_count=}{Colors.END};")
                time.sleep(0.05)
                print(f"{Colors.BLUE}   - {total_found=}{Colors.END};")
                time.sleep(0.05)
                print(f"{Colors.BLUE}   - {len(avaible_sites)=}{Colors.END};")
                time.sleep(0.05)
        except Exception as error:
            with open("last_launch.log", "a") as file:
                file.write(f"[LOG] <<ERROR>> - Error while saving progress: {error}\n")
            print(f"{Colors.RED}[LOG] <<ERROR>>{Colors.END} - Error while saving progress: {error}\n")
            time.sleep(0.05)
    
    def load_progress(self, progress_file):
        try:
            with open(progress_file, "rb") as f:
                progress, avaible, total_errors_count, total_found = pickle.load(f)
                with open("last_launch.log", "a") as file:
                    file.write(f"[LOG] <<LOAD>> - last progress loaded from {progress_file}\n")
                print(f"{Colors.GREEN}[LOG] <<LOAD>>{Colors.END} - last progress loaded from {progress_file}")
                time.sleep(0.05)
                return progress, avaible, total_errors_count, total_found
        except Exception as error:
            with open("last_launch.log", "a") as file:
                file.write(f"[LOG] <<ERROR>> Error while load progress: {error}\n")
            print(f"{Colors.RED}[LOG] <<ERROR>>{Colors.END} Error while load progress: {error}\n")
            time.sleep(0.05)
            return None,None,None,None
    
    def is_file_created_more_than_3h_ago(self, file_path):
        try:
            if not os.path.exists(file_path):
                return True
            created_time = os.path.getctime(file_path)
            current_time = time.time()
            time_difference = current_time - created_time
            if time_difference > 36000:
                return True
            else:
                return False
        except Exception as error:
            print(f"\n{Colors.RED}[LOG] <<Error>>{Colors.END} - Error occured: {error}...")
            time.sleep(0.05)
    
    @staticmethod
    def check_website(url, valid_proxy):
        if valid_proxy:
            proxies = {"http": valid_proxy, "https": valid_proxy}
        else:
            proxies = None
        try:
            ua = UserAgent()
            headers = {'User-Agent': ua.random}
            response = requests.get(url=url, headers=headers, timeout=5, stream=True, proxies=proxies)

            if str(response.status_code)[0] == "2":
                return (True, response.status_code, "Success", url, response.content.decode('utf-8'))
            elif str(response.status_code)[0] == "3":
                return (False, response.status_code, "Redirection", url, response.content.decode('utf-8'))
            elif response.status_code == 400:
                return (False, response.status_code, "Bad Request", url, response.content.decode('utf-8'))
            elif response.status_code == 401:
                return (False, response.status_code, "Unauthorized", url, response.content.decode('utf-8'))
            elif response.status_code == 402:
                return (False, response.status_code, "Payment Required", url, response.content.decode('utf-8'))
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
            return (False, 0, "requests.exceptions.ConnectionError", url, "")
        except urllib3.exceptions.MaxRetryError:
            return (False, 0, "urllib3.exceptions.MaxRetryError", url, "")
        except requests.exceptions.ReadTimeout:
            return (False, 0, "requests.exceptions.ReadTimeoutError", url, "")
        except Exception as error:
            return (False, 0, str(error), url, "")
        return (False, response.status_code, "Status not assigned", url, response.content.decode('utf-8'))

    def handle_sigint(self, signum, frame):
        try:
            print(f"\n{Colors.RED}[LOG] <<Received SIGINT>>{Colors.END} - terminating...")
            time.sleep(0.05)
            status_string = f"{round(self.current_percentage, 2)}%_[{self.current_iteration}of{self.current_total_iterations}]"
            tmp_output_file = self.output_file.replace(self.your_site, f"{self.your_site}_{status_string}").replace("Results/DirpathFinder_Results/", "Results/TMP_DirpathFinder_Results/")
            with open("last_launch.log", "a") as file:
                file.write(f"[Ctrl+C 'Error'] <<CTRL+C Detected>> - Temporary result saved to '{tmp_output_file}'\n")
            self.write_results_to_file(self.available_sites, tmp_output_file)
            progress_output_file = f"Progress/{self.your_site}_{self.paths_dictionary.replace('Dictionary/', '').replace('.txt', '')}.pickle"
            self.save_progress(progress_output_file, self.current_iteration, self.available_sites, self.total_errors_count, self.total_found)
            self.keep_highest_percentage_files()
            os._exit(1)
        except Exception as error:
            print(f"\n{Colors.RED}[LOG] <<Error>>{Colors.END} - Error occured: {error}...")
            time.sleep(0.05)

    def start_dir_scanner(self):
        try: 
            with open(self.paths_dictionary, "r") as file:
                paths_prefixs = file.readlines()
            paths_prefixs = [f"http://{self.your_site}/{path.strip()}" for path in paths_prefixs]
        except Exception as error:
            print(f"\n{Colors.RED}[LOG] <<Error>>{Colors.END} - Error occured: {error}...")
            time.sleep(0.05)

        try:
            signal.signal(signal.SIGINT, self.handle_sigint)
            total_sites = len(paths_prefixs)
            self.current_total_iterations = total_sites
            with tqdm(total=total_sites, desc="Checking dirs in domain", initial=self.current_iteration) as self.pbar:
                while self.current_iteration < len(paths_prefixs):
                    threads_number = min(self.max_threads_number, len(paths_prefixs) - self.current_iteration)
                    results = self.launch_threadings(paths_prefixs, threads_number)
                    for result in results:
                        #self.current_iteration = pbar.n #Для передачи в pickle в случае остановки
                        self.current_percentage = self.pbar.n / total_sites * 100
                        status, status_code, description, url, page_content = result[0], result[1], result[2], result[3], result[4]

                        if self.exclude_flag_phrase and self.exclude_flag_phrase in page_content:
                            status = False
                            description = f"Exclude phrase found: '{self.exclude_flag_phrase}'"
                            status_code = f"{str(status_code)}:False"
                        self.current_iteration += 1
                        if "Error" in description:
                            self.total_errors_count += 1
                            self.errors_dict[self.total_errors_count] = time.time()

                        with open("last_launch.log", "a") as file:
                            file.write(f"[{status_code}] - <<{description}>> - {url}\n")
                        if status:
                            self.available_sites.append(url)
                            self.total_found += 1
                        
                        self.pbar.set_postfix_str(f"{url}")
                        self.pbar.set_description(f"Checking status. Errors: {self.total_errors_count}; Found: {self.total_found}") 
                        self.pbar.update(1)
                        time.sleep(0.03)
                    self.pbar.update(1)

                    check_errors_result, tqdm_desc = self.check_errors()
                    if tqdm_desc:
                        tqdm.write(tqdm_desc)
                    if not check_errors_result:
                        self.pbar.n = self.current_iteration
                        if self.use_proxy:
                            tqdm.write(f"{Colors.BLUE}[LOG] <<INFO>>{Colors.END} - Valid proxy searcher starts")
                            self.find_valid_proxy("proxy_list.txt")
                            if self.valid_proxy:
                                tqdm.write(f"{Colors.GREEN}[LOG] <<SUCCESS>>{Colors.END} - Founded valid proxy: {self.valid_proxy}")
                            else:
                                tqdm.write(f"{Colors.RED}[LOG] <<ERROR>>{Colors.END} - No valid proxy founded. Setting `use_proxy` to False")
                                self.use_proxy = False
                        else:
                            for i in range(self.seconds_to_sleep):
                                self.pbar.set_description(f"[LOG] <<SLEEPING>> - {Colors.BLUE}{self.seconds_to_sleep-i}{Colors.END} seconds remaining...")
                                time.sleep(1)

            self.write_results_to_file(self.available_sites, self.output_file)
        
        except KeyboardInterrupt:
            print(f"\n{Colors.RED}[LOG] <<KeyboardInterrupt received>>{Colors.END} - terminating...")
            time.sleep(0.05)
            with open("last_launch.log", "a") as file:
                file.write("[LOG] - <<KeyboardInterrupt received>> terminating...\n")
            status_string = f"{round(self.current_percentage, 2)}%_[{self.current_iteration}of{self.current_total_iterations}]"
            tmp_output_file = self.output_file.replace(self.your_site, f"{self.your_site}_{status_string}").replace("Results/DirpathFinder_Results/", "Results/TMP_DirpathFinder_Results/")
            self.write_results_to_file(self.available_sites, tmp_output_file)
            progress_output_file = f"Progress/{self.your_site}_{self.paths_dictionary.replace('Dictionary/', '').replace('.txt', '')}.pickle"
            self.save_progress(progress_output_file, self.current_iteration, self.available_sites, self.total_errors_count, self.total_found)
            self.keep_highest_percentage_files()
        # except Exception as error:
        #     print(f"\n{Colors.RED}[LOG] <<Thread Error>>{Colors.END} - Error occured: {error}...")
        #     print(error)
        #     with open("last_launch.log", "a") as file:
        #         file.write(f"\n[LOG] <<Thread Error>> - Error occured: {error}...")

    def launch_threadings(self, paths_prefixs, threads_number):
        results = []
        threads = []
        for i in range(threads_number):
            thread = threading.Thread(target=self.process_url, args=(paths_prefixs[self.current_iteration + i], results))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        return results
    
    def process_url(self, url, results):
        try:
            result = self.check_website(url, self.valid_proxy)
            results.append(result)
        except Exception as error:
            print(f"{Colors.RED}[LOG] <<THREAD ERROR>>{Colors.END} - Error occured: {error}")
            time.sleep(0.05)
    
    def write_results_to_file(self, results, output_file):
        try:
            if results:
                with open(output_file, "w") as file:
                    file.write("\n".join(results))
                print(f"{Colors.GREEN}[LOG] <<SAVE>>{Colors.END} - Results written to:", output_file)
                time.sleep(0.05)
                with open("last_launch.log", "a") as file:
                    file.write(f"[LOG] - Results written to: '{output_file}'\n")
            else:
                if "TMP" in output_file:
                    with open(output_file, "w") as file:
                        file.write("\n".join(results))
                    print(f"{Colors.GREEN}[LOG] <<SAVE>>{Colors.END} - TMP Results written to:", output_file)
                    time.sleep(0.05)
                    with open("last_launch.log", "a") as file:
                        file.write(f"[LOG] - TMP Results written to: '{output_file}'\n")
                else:
                    print(f"{Colors.YELLOW}[LOG] <<No Data>>{Colors.END} - No results to write.")
                    time.sleep(0.05)
                    with open("last_launch.log", "a") as file:
                        file.write(f"[LOG] <<No Data>> - No results to write.\n")
        except Exception as error:
            print(f"\n{Colors.RED}[LOG] <<Error>>{Colors.END} - Error occured: {error}...")
            time.sleep(0.05)
    
    def keep_highest_percentage_files(self):
        try:
            removed_flag = False
            folder_path = "Results/TMP_DirpathFinder_Results"
            # Создаем словарь для хранения наибольших процентов для каждого сайта
            max_percentages = {}

            # Получаем список файлов в указанной папке
            files = os.listdir(folder_path)

            # Проходим по каждому файлу
            for file_name in files:
                # Проверяем, что файл имеет ожидаемый формат
                if "_" not in file_name or "%" not in file_name:
                    continue

                # Извлекаем название сайта и процент из имени файла
                parts = file_name.split("_")
                site_name = parts[0]
                percentage_str = parts[1]
                
                # Обрабатываем случай, если процент содержит символы, отличные от цифр и точки
                try:
                    percentage = float(percentage_str[:-1])
                except ValueError:
                    continue

                # Ищем последнее число в имени файла с помощью регулярного выражения
                last_number_match = re.search(r'(\d+)of(\d+)', file_name)
                if last_number_match:
                    last_number = int(last_number_match.group(2))
                else:
                    continue

                # Добавляем имя файла и процент к списку для данного сайта
                if site_name in max_percentages:
                    max_percentages[site_name].append((percentage, last_number, file_name))
                else:
                    max_percentages[site_name] = [(percentage, last_number, file_name)]

            # Проходим по каждому сайту и оставляем файлы с наибольшим процентом для каждого последнего числа
            for site_name, files_info in max_percentages.items():
                # Сортируем файлы по проценту в убывающем порядке
                files_info.sort(reverse=True)
                # Оставляем только файлы с максимальным процентом для каждого последнего числа
                selected_files = set()
                for info in files_info:
                    _, last_number, file_name = info
                    if last_number not in selected_files:
                        selected_files.add(last_number)
                    else:
                        os.remove(os.path.join(folder_path, file_name))
                        removed_flag = True

            if removed_flag:
                print(f"{Colors.GREEN}[LOG] <<DELETE>>{Colors.END} - Ненужные TMP файлы удалены.")
                time.sleep(0.05)
        except Exception as error:
            print(f"\n{Colors.RED}[LOG] <<Error>>{Colors.END} - Error occured: {error}...")
            time.sleep(0.05)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Автоматизированный поиск директорий')
    parser.add_argument('-d', '--dictionary_path', type=str, default='Dictionary/dict_13k_dirs.txt', help='Путь к словарю директорий (по умолчанию: Dictionary/dict_13k_dirs.txt)')
    parser.add_argument('-u', '--url', type=str, default=None, help='Ссылка на домен для поиска директорий')
    parser.add_argument('-s', '--sleep_seconds', type=int, default=30, help='Количество секунд для сна при возникновении множетсва ошибок')
    parser.add_argument('-e', '--sleep_errors', type=int, default=30, help='Количество ошибок в 30сек для срабатывания сна')
    parser.add_argument('-t', '--threads_number', type=int, default=10, help='Максимальное количество потоков программы')
    parser.add_argument('-ep', '--exclude_phrase', type=str, default=None, help='Фраза для отнесения 200-запросов к недостпным')
    parser.add_argument('-up', '--use_proxy', type=str, default="False", help='Использовать прокси-список')
    parser.add_argument('-se', '--skip_errors', type=str, default="False", help='Не перепроверять сайты, свалившиеся с ошибкой')
    
    args = parser.parse_args()

    paths_dictionary = args.dictionary_path
    domain = args.url
    sleep_seconds = args.sleep_seconds
    max_errors_number = args.sleep_errors
    max_threads_number = args.threads_number
    exclude_phrase = args.exclude_phrase
    use_proxy = args.use_proxy
    skip_errors_flag = args.skip_errors
    if "y" in skip_errors_flag.lower() or "true" in skip_errors_flag.lower():
        skip_errors_flag = True
    else:
        skip_errors_flag = False
    if "true" in use_proxy.lower() or "y" in use_proxy.lower():
        use_proxy = True
    else:
        use_proxy = False
    if not domain:
        while not domain:
            domain = input(f"Enter domain for scan:\n[INPUT] >").replace("https://", "").replace("http://", "")
    domain = domain.replace("https://", "").replace("http://", "")
    
    if not os.path.exists(paths_dictionary):
        print(f"{Colors.YELLOW}[LOG] <<NOT EXISTS>>{Colors.END} Dictionary `{paths_dictionary}` does not exists")
        time.sleep(0.05)
        print(f"{Colors.YELLOW}[LOG] <<SET VAR>>{Colors.END} Set dictionary to `Dictionary/dict_13k_dirs.txt`")
        time.sleep(0.05)
        paths_dictionary = "Dictionary/dict_13k_dirs.txt"

    Finder = DirPathFinder(your_site=domain, paths_dictionary=paths_dictionary, seconds_to_sleep=sleep_seconds, max_errors_number=max_errors_number, max_threads_number=max_threads_number, exclude_flag_phrase=exclude_phrase, use_proxy=use_proxy, skip_errors_flag=skip_errors_flag)
    Finder.start_dir_scanner()
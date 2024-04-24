import re
import os
import colorama
from colorama import Style, Fore
import chardet
import argparse

class SecretSearcher:
    def __init__(self, file_path=None, show_comments=False) -> None:
        self.file_path = file_path
        self.show_comments = show_comments

        if not os.path.exists(self.file_path):
            while not os.path.exists(self.file_path):
                self.file_path = input("Введите путь к файлу для поиска: ")
                
        # Определяем паттерны для поиска
        self.patterns = {
            '[google_api]'     : r'AIza[0-9A-Za-z-_]{35}',
            '[firebase]'  : r'AAAA[A-Za-z0-9_-]{7}:[A-Za-z0-9_-]{140}',
            '[google_captcha]' : r'6L[0-9A-Za-z-_]{38}|^6[0-9a-zA-Z_-]{39}$',
            '[google_oauth]'   : r'ya29\.[0-9A-Za-z\-_]+',
            '[amazon_aws_access_key_id]' : r'A[SK]IA[0-9A-Z]{16}',
            '[amazon_mws_auth_token]' : r'amzn\\.mws\\.[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
            '[amazon_aws_url]' : r's3\.amazonaws.com[/]+|[a-zA-Z0-9_-]*\.s3\.amazonaws.com',
            '[amazon_aws_url2]' : r"(" \
                r"[a-zA-Z0-9-\.\_]+\.s3\.amazonaws\.com" \
                r"|s3://[a-zA-Z0-9-\.\_]+" \
                r"|s3-[a-zA-Z0-9-\.\_\/]+" \
                r"|s3.amazonaws.com/[a-zA-Z0-9-\.\_]+" \
                r"|s3.console.aws.amazon.com/s3/buckets/[a-zA-Z0-9-\.\_]+)",
            '[facebook_access_token]' : r'EAACEdEose0cBA[0-9A-Za-z]+',
            '[authorization_basic]' : r'basic [a-zA-Z0-9=:_\+\/-]{5,100}',
            '[authorization_bearer]' : r'bearer [a-zA-Z0-9_\-\.=:_\+\/]{5,100}',
            '[authorization_api]' : r'\bapi\s*[:=]+\s*[a-zA-Z0-9_\-]{5,100}\b|\bkey\s*[:=]+\s*[a-zA-Z0-9_\-]{5,100}\b',
            '[mailgun_api_key]' : r'\bkey\s*[:=]+\s*[0-9a-zA-Z]{32}\b',
            '[twilio_api_key]' : r'\bSK\s*[:=]+\s*[0-9a-fA-F]{32}\b',
            '[twilio_account_sid]' : r'\bAC\s*[:=]+\s*[a-zA-Z0-9_\-]{32}\b',
            '[twilio_app_sid]' : r'\bAP\s*[:=]+\s*[a-zA-Z0-9_\-]{32}\b',
            '[paypal_braintree_access_token]' : r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}',
            '[square_oauth_secret]' : r'sq0csp-[ 0-9A-Za-z\-_]{43}|sq0[a-z]{3}-[0-9A-Za-z\-_]{22,43}',
            '[square_access_token]' : r'sqOatp-[0-9A-Za-z\-_]{22}|EAAA[a-zA-Z0-9]{60}',
            '[stripe_standard_api]' : r'sk_live_[0-9a-zA-Z]{24}',
            '[stripe_restricted_api]' : r'rk_live_[0-9a-zA-Z]{24}',
            '[github_access_token]' : r'[a-zA-Z0-9_-]*:[a-zA-Z0-9_\-]+@github\.com*',
            '[rsa_private_key]' : r'-----BEGIN RSA PRIVATE KEY-----',
            '[ssh_dsa_private_key]' : r'-----BEGIN DSA PRIVATE KEY-----',
            '[ssh_dc_private_key]' : r'-----BEGIN EC PRIVATE KEY-----',
            '[pgp_private_block]' : r'-----BEGIN PGP PRIVATE KEY BLOCK-----',
            '[json_web_token]' : r'ey[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*$',
            '[slack_token]' : r"\"api_token\":\"(xox[a-zA-Z]-[a-zA-Z0-9-]+)\"",
            '[SSH_privKey]' : r"([-]+BEGIN [^\s]+ PRIVATE KEY[-]+[\s]*[^-]*[-]+END [^\s]+ PRIVATE KEY[-]+)",
            '[possible_Creds]' : r"(?i)(" \
                            r"password\s*[`=:\"]+\s*[^\s]+|" \
                            r"password is\s*[`=:\"]*\s*[^\s]+|" \
                            r"pwd\s*[`=:\"]*\s*[^\s]+|" \
                            r"passwd\s*[`=:\"]+\s*[^\s]+)",
            '[Токен Apple Push Notification Service]': r'\b(?:APNS|apns_token)\s*[:=]\s*[\'"]?([A-F0-9]{64})[\'"]?,',
            '[Токен WordPress]': r'\b(?:wordpress_token|wp_token)\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[Токен Magento]': r'\b(?:magento_token|mg_token)\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[Токен OWASP ZAP]': r'\b(?:owasp_zap_token|zap_token)\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[Токен Prometheus]': r'\b(?:prometheus_token)\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[Токен Grafana]': r'\b(?:grafana_token)\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[Токен Google Metrics]': r'\b(?:google_metrics_token|metrics_token)\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[Номер телефона]': r'\b(?:\+7|8)[ -]?\(?(?:\d{3})\)?[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}\b,',
            '[Номер карты (luna)]': r'\b(?:\d[ -]*?){13,16}\b',
            '[Ссылки]': r'\b(?<!@)(?:https?:\/\/)?(?:www\.)?[-a-zA-Z0-9:%._\+~#=]{2,256}\.(?:com|ru|org|рф|gov|edu|mil|int|biz|aero|coop|museum|arpa|travel|asia|cat|jobs|mobi|tel|xxx)(?:\/[-a-zA-Z0-9@:%_\+.~#?&//=]*)?\b(?!@)',
            '[Имена файлов]': r'\b\w+\.(?:txt|js|doc|docx|pdf|xls|xlsx|ppt|pptx|csv|json|xml|html|htm|rtf|odt|ott|ods|odp|ott|tif|tiff|mp3|wav|aac|ogg|flac|wma|mp4|avi|wmv|mkv|mov|flv|mpeg|zip|rar|7z|tar|gz|bz2)\b',
            '[Даты]': r'\b(?:\d{2}[.-]\d{2}[.-]\d{4}|\d{4}[.-]\d{2}[.-]\d{2}|\d{2}:\d{2}:\d{4})\b',
            '[Email адреса]': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            '[Хеш-суммы (MD5, SHA-1, SHA-256)]': r'\b(?:[a-fA-F\d]{32}|[a-fA-F\d]{40}|[a-fA-F\d]{64})\b',
            '[API ключи]': r'\b[A-Za-z0-9]{8}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{4}-[A-Za-z0-9]{12}\b',
            '[Telegram API-key]': r'\b\d{10}:[a-zA-Z0-9_-]{35}\b',
            '[SSH ключи]': r'\b(?:ssh-rsa|ssh-dss|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521)\s+[A-Za-z0-9+/]+(?:[=]{0,3})(?: [^@]+@[^@]+)?\b',
            '[SSL сертификаты]': r'-----BEGIN CERTIFICATE-----(?:.|\s)*?-----END CERTIFICATE-----',
            '[IPv4 адреса]': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            '[IPv6 адреса]': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            '[MAC адреса]': r'\b(?:[0-9A-Fa-f]{2}[:-]){5}(?:[0-9A-Fa-f]{2})\b',
            '[СНИЛС]': r'\b\d{3}(?:-|\s)?\d{3}(?:-|\s)?\d{3}(?:\s)?\d{2}\b',
            '[Паспорт]': r'\b\d{4}(?:[ -]|\s)\d{6}\b,',
            '[VIN номера]': r'\b(?:[A-HJ-NPR-Z0-9]{17})\b',
            '[IMEI номера]': r'\b(?:\d{15})\b',
            '[Конфигурационные файлы сервера]': r'\b(?:server.conf|config.ini|settings.json)\b',
            '[Координаты]': r'\b\d{2}\.\d+,\s\d{2}\.\d+\b',
            '[Логин БД]': r'\b(?:username|login|user|email)\s*=\s*[\'"]?(\w+)[\'"]?,',
            '[Токен OAuth]': r'\b(?:OAuth|Bearer)\s+([A-Za-z0-9-_]+)\b,',
            '[Ключ Facebook API]': r'\b(?:facebook|fb)_app_id\s*[:=]\s*[\'"]?([0-9]+)[\'"]?,',
            '[CSRF токен]': r'\bcsrf_token\s*[:=]\s*[\'"]?([A-Za-z0-9]+)[\'"]?,',
            '[AES ключ]': r'\b(?:AES|aes_key)\s*[:=]\s*[\'"]?([A-Za-z0-9+/=]+)[\'"]?,',
        }

    @staticmethod
    def convert_to_utf8(input_file):
        output_file = f"{input_file}.txt"
        # Определение кодировки входного файла
        with open(input_file, 'rb') as f:
            rawdata = f.read()
            encoding = chardet.detect(rawdata)['encoding']

        if encoding is None:
            encoding = 'utf-8'  # По умолчанию, если не удалось определить

        # Переконвертация в utf-8
        with open(input_file, 'r', encoding=encoding, errors='ignore') as f:
            content = f.read()
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f'[LOG] <<Success>> - Файл переконвертирован в UTF-8')
        return output_file
    
    def search_sensitive_info(self):
        found_info = {}
        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = file.read()

        except UnicodeDecodeError as error:
            print(f'[LOG] <<UnicodeDecodeError>> - {error}')
            print(f'[LOG] <<Fix>> - Попытка конвертации в UTF-8')
            self.file_path = self.convert_to_utf8(self.file_path)
            
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = file.read()

        for category, pattern in self.patterns.items():
            matches = re.findall(pattern, data)
            if matches:
                found_info[category] = matches

        return found_info

    def find_comments_and_usernames_in_code(self):
        russian_letters = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
        russian_letters += russian_letters.upper()  # Добавляем верхний регистр

        with open(self.file_path, 'r', encoding="utf-8") as file:
            for line in file:
                # Паттерн для комментариев
                comment_pattern = r'(\/\*[\s\S]{1,50}?\*\/|\/\/.{1,50}|<!--[\s\S]{1,50}?-->)'
                comments = re.findall(comment_pattern, line)
                for comment in comments:
                    # Проверка наличия русских букв в комментарии и длины менее 50 символов
                    if (any(letter in comment for letter in russian_letters) and
                            len(comment) <= 50) and "loaded from" not in comment:
                        print(Fore.GREEN + comment.strip() + Style.RESET_ALL)
                        print()  # Добавляем пустую строку после каждого комментария

                        # Паттерн для юзернеймов
                        username_pattern = r'\B@[a-zA-Z0-9_-]+\b'
                        usernames = re.findall(username_pattern, comment)
                        for username in usernames:
                            print(Fore.BLUE + "Found username:", username + Style.RESET_ALL)

    def search_information(self):
        colorama.init()
        try:
            sensitive_info = self.search_sensitive_info()
            
            if sensitive_info:
                print("Найденная sensitive информация:")
                for category, matches in sensitive_info.items():
                    # Вывод информации с цветом
                    print(f"\n{colorama.Fore.YELLOW}{category}{colorama.Style.RESET_ALL}: {', '.join(matches)}")
            else:
                print("Нет найденной sensitive информации.")
            if self.show_comments:
                self.find_comments_and_usernames_in_code()

        except FileNotFoundError:
            print("Указанный файл не найден.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Автоматизированный поиск чувствительной информации')
    parser.add_argument('-f', '--file_path', type=str, default=None, help='Путь к файлу для поиска информации')
    parser.add_argument('-s', '--show_comments', type=str, default=False, help='Вывод комментариев в коде, которые содержат фразы на русском языке')
    args = parser.parse_args()
    file_path = args.file_path.replace('"', "")
    show_comments = args.show_comments
    if "true" in show_comments.lower() or "yes" in show_comments.lower():
        show_comments = True

    if not os.path.exists(file_path):
        while not os.path.exists(file_path):
            file_path = input(f"This file does not exists. Try again:\n>").replace('"', "")
    Searcher = SecretSearcher(file_path=file_path, show_comments=show_comments)
    Searcher.search_information()
# Гайд по использованию скриптов
Все скрипты адаптированы к использованию, как в консоли, так и импортируя в Python, как модули.

## Оглавление:
[**1. SubdomainsFinder**](#SubdomainsFinder)

[**2. DirPathFinder**](#DirPathFinder)

[**3. SecretSearcher**](#SecretSearcher)

[**4. JadxToText**](#JadxToText)

## 1) SubdomainsFinder <a name = "SubdomainsFinder"></a>
Скрипт для выявления под-доменов, основан на API сервиса SecurityTrails. 

**Использование в консоли:**
```console
user:~$ python SubdomainsFinder.py -u YOUR_SITE -t SECURITY_TRAILS_API_TOKEN
```

**Пример использования в Python:**
```python
from SubdomainsFinder import SubdomainsFinder

sites = ["google.com", "example.ru"]
api_key = "Some_Api_Token"

for site in sites:
    Finder = SubdomainsFinder(site=site, securitytrails_api_key=api_key)
    Finder.start_aviability_scanner()
```
По умолчанию результаты сохраняются в директорию `/Results` (создаётся при первом запуске, если таковой нет). 

* Результаты от SecurityTrails - в каталоге `Results/SubdomainsFinder_RawResults`, 
* Валидные под-домены в `Results/SubdomainsFinder_FinalResults`

По умолчанию SecurityTrails-токен берется из файла `config.json` --> если он там есть, можно не указывать параметр `-t` в запросе.

## 2) DirPathFinder <a name = "DirPathFinder"></a>
Скрипт для выявления директорий (в том числе скрытых). 

Использует многопоточность `threading`, сериализацию данных (сохранение прогресса), при помощи модуля `pickle`. 

Имеется возможность прерывания работы программы нажатием `CTRL+C`, а также засыпание программы в случае возникновения большого количества ошибок. 

**Использование в консоли:**
```console
user:~$ python DirPathFinder.py -u google.com
[LOG] <<INFO>> Program launched with 10 threads
[LOG] <<INFO>> Domain for scan: 'google.com'
[LOG] <<INFO>> Dictionary: 'Dictionary/dict_13k_dirs.txt'
[LOG] <<LOAD>> - last progress loaded from Progress/google.com_dict_13k_dirs.pickle
```
**Дополнительные параметры:**

`-d, --dictionary_path` - Путь к словарю с директориями, **по умолчанию: Dictionary/dict_13k_dirs.txt**

`-u, --url` - Ссылка на домен для поиска директорий, **обязательный параметр**

`-s, --sleep_seconds` - Количество секунд для сна при возникновении множетсва ошибок, **по умолчанию: `30`**

`-e, --sleep_errors` - Количество ошибок в 30сек для срабатывания сна, **по умолчанию: `30`**

`-t, --threads_number` - Максимальное количество потоков программы, **по умолчанию: `10`**

`-up, --use_proxy` - Использовать прокси, в случае блокировки со стороны сервера, **по умолчанию: `False`**

`-se, --skip_errors` - Пропустить и не перепроверять сайты, свалившиеся с ошибкой (sleep_errors), **по умолчанию: `True`**

`-ep, --exclude_phrase` - Фраза для исключения успешных запросов из результатов. Пример: сайт выдает код ответа `[200]`, но по факту возвращает HTML-страницу с текстом "Такой страницы не существует". Соответственно, в `exclude_phrase` можно вписать фразу "Такой страницы не существует", чтобы скрипт относил такие страницы, как к невалидным. Поиск фразы осуществляется в `response.content`, соответственно фраза может быть хоть html-кодом, хоть base64 картинкой. **По умолчанию: `None`**

**Пример использования в Python:**
```python
from DirPathFinder import DirPathFinder

#Определяем параметры
domain = "google.com"
paths_dictionary = "Dictionary/dict_4600_dirs.txt"
seconds_to_sleep = 300
use_proxy = False
max_errors_number = 30
max_threads_number = 20
exclude_phrase = "404"

#Инициализация класса
Finder = DirPathFinder(your_site=domain, paths_dictionary=paths_dictionary, seconds_to_sleep=sleep_seconds, max_errors_number=max_errors_number, use_proxy=use_proxy, max_threads_number=max_threads_number, exclude_flag_phrase=exclude_phrase)

#Запуск сканера
Finder.start_dir_scanner()
```

#### ВАЖНО!!!
При нажатии `CTRL+C` - программа сохраняет временные результаты, такие как: 
* **Прогресс.** Сохраняется в директории `Progress`, имеют вид: `google.com_dict_13k_dirs.pickle`, в которой указан сайт и словарь, по которому производилось сканирование.
* **Уже найденные под-домены.** Сохраняются в директории `Results/TMP_DirpathFinder_Results`. Имеют вид: `google.com_12.4%_[1622of13180]_AvailablePaths.txt`, по названию файла можно узнать дополнительную информацию.

### Прогресс
Если существует такой pickle файл, как `google.com_dict_13k_dirs.pickle`, и пользователем производится запуск сканирования домена **google.com** при помощи словаря `13k_dirs`, то прошлый прогресс будет загружен и сканирование продолжится с момента прошлой остановки программы. 

(Если нужно начать сканирование с нуля - можно удалить/перенести файл прогресса `pickle`)

### Логи
Логирование происходит в файл `last_launch.log`, по нему можно просто ориентироваться что пошло не так, какие ошибки и коды возвращал каждый из сайтов. Лог выглядит следующим образом:
```js
[2024-04-12 14:30:22] DirpathFinder Started..
[200] - <<Success>> - http://example.com
[403] - <<Forbidden>> - http://example.com/access.log
[0] - <<requests.exceptions.ConnectionError>> - http://example.com.vmachine
[Ctrl+C 'Error'] <<CTRL+C Detected>> - Temporary result saved to 'Results/TMP_DirpathFinder_Results///example.com_32.49%_[4282of13179]_AvailablePaths.txt'
```


## 3) SecretSearcher <a name = "SecretSearcher"></a>
Автоматизированный поиск чувствительной информации в файлах. Скрипт ищет такую информацию, как:
![Screenshot_2](https://github.com/ILYXAAA/web-scan-tools/assets/107761814/7dbd4637-08ce-427b-85d7-6a7b80c7d28a)

Полный список можно посмотреть в файле `SecretSearcher.py`

**Использование в консоли:**
```console
user:~$ python SecretSearcher.py -f path_to_file.txt -s True
```
* `-f, --file_path` - Путь к файлу для поиска информации. Обязательный параметр
* `-s, --show_comments` - Вывод комментариев в коде, которые содержат фразы на русском языке. По умолчанию: False

**Пример использования в Python:**
```python
from SecretSearcher import SecretSearcher

files_list = ["file_1.js", "file_2.txt", "file_3.json"]
show_comments = True

for file in files_list:
    Searcher = SecretSearcher(file_path=file_path, show_comments=show_comments)
    Searcher.search_information()
```

## 4) JadxToText <a name = "JadxToText"></a>
Инструмент для склеивания всех `.java` файлов, получаемых после декомпиляции apk файла в программе `JadX`. 

**[В программе JadX]**: По умолчанию после декомпиляции всех классов - создается папка `source`, в которой должны быть все декомпилированные файлы мобильного приложения. 

Скрипт `JadxToText` рекурсивно проходится по всем папкам внутри директории `source` - после чего сохраняет код всех `.java` файлов в один `txt` файл. Этот файл, к примеру, в последствии можно проанализировать при помощи `SecretSearcher`.

**Использование в консоли:**
```console
user:~$ python JadxToText.py -s path_to_source_folder -o output_file.txt
```

**Пример использования в Python:**
```python
from JadxToText import JadxToText

sources_list = [("Google", "GoogleMusicAPK_source_folder"), ("VK", "VKMusic_source_folder")]

for source_tuple in sources_list:
    service, source_path = source_tuple
    output_file = f"{service}.txt"

    Jadx = JadxToText(source_folder=source_path, output_file=output_file)
    Jadx.merge_source_to_txt()
```

import requests
import re
import time

USER_COOKIE = "9320c05a78627ad649cc421c79d34a6e"
HOST = "hw1.alexbers.com"
PORT = 80

TASK_TYPES = {
    "GET": "Отправьте GET-запрос по адресу",
    "POST": "Отправьте POST-запрос по адресу",
    "FILE": "Загрузите файлы по адресу",
    "LINK": "Перейдите по",
}
TABLE_MARKERS = {
    "query_params": "При переходе выставьте следующие параметры запроса, указанные в таблице",
    "headers": "Запрос должен иметь следующие заголовки",
    "cookies": "В запросе должны быть выставлены cookie",
    "form_data": "Запрос должен иметь следующие данные формы",
    "files": "Имя файла"
}

def extract_table(html_chunk):
    rows = re.findall(r'<tr>(.*?)</tr>', html_chunk, re.DOTALL)
    result = {}

    for row in rows[1:]:
        cells = re.findall(r'<t[dh]>(.*?)</t[dh]>', row, re.DOTALL)
        key = re.sub(r'<[^>]+>', '', cells[0]).strip()
        value = re.sub(r'<[^>]+>', '', cells[1]).strip()
        result[key] = value

    return result

def parse_html_page(html_code):
    if "Секретный ключ" in html_code:
        flag_match = re.search(r'<code>(.*?)</code>', html_code, re.IGNORECASE)
        flag = flag_match.group(1).strip() if flag_match else "Не удалось найти тег <code> с ключом."
        return "DONE", flag, None

    current_task = None
    for method, instruction in TASK_TYPES.items():
        if instruction in html_code:
            current_task = method
            break

    if not current_task:
        raise Exception(f"Неизвестный тип задания на странице:\n{html_code}")

    path = "/"
    if current_task == "LINK":
        link_match = re.search(r'<a\s+[^>]*?href=["\'](.*?)["\']', html_code, re.IGNORECASE)
        if link_match:
            path = link_match.group(1)
    else:
        address_match = re.search(r'<code[^>]*>(.*?)</code>', html_code)
        if address_match:
            path = address_match.group(1)

    parsed_data = {
        "query_params": {},
        "headers": {},
        "cookies": {},
        "form_data": {},
        "files": {}
    }

    blocks = html_code.split("</table>")
    for block in blocks:
        for key, marker in TABLE_MARKERS.items():
            if marker and marker in block:
                table_dict = extract_table(block)
                parsed_data[key].update(table_dict)
                break

    return current_task, path, parsed_data

def get_html_code(method, path, query_params=None, headers=None, cookies=None, form_data=None, file_data=None):
    if path.startswith("http"):
        full_url = path
    else:
        clean_path = path.lstrip("/")
        full_url = f"http://{HOST}/{clean_path}"

    actual_method = "GET" if method == "LINK" else ("POST" if method == "FILE" else method.upper())

    request_params = query_params if query_params else ""

    request_headers = {"Connection": "Close"}
    if headers:
        request_headers.update(headers)

    request_cookies = {"user": USER_COOKIE}
    if cookies:
        request_cookies.update(cookies)

    kwargs = {
        "params": request_params,
        "headers": request_headers,
        "cookies": request_cookies
    }

    if method == "POST":
        kwargs["data"] = form_data

    elif method == "FILE":
        parts = {}
        for name, content in file_data.items():
            parts[name] = (name, content)
        kwargs["files"] = parts

    response = requests.request(actual_method, full_url, **kwargs)
    return response.text if response else None

def main():
    print("Запуск прохождения")
    current_path = "/"
    current_method = "GET"
    parsed_data = {
        "query_params": {},
        "headers": {},
        "cookies": {},
        "form_data": {},
        "files": {}
    }

    while True:
        try:
            print(f"Запрос: {current_method} к {current_path}")
            html_code = get_html_code(current_method, current_path, parsed_data["query_params"], parsed_data["headers"],
                                     parsed_data["cookies"], parsed_data["form_data"], parsed_data["files"])
            current_method, current_path, parsed_data = parse_html_page(str(html_code))

            if current_method == "DONE":
                print("=========")
                print("КВЕСТ ПРОЙДЕН!")
                print(f"Секретный ключ: {current_path}")
                print("=========")
                break

            print(f"Успешно обработано {parsed_data}")
            print("********")

        except Exception as e:
            print("_________")
            print(f"Случилась ошибка: {e}, повторная попытка")
            print("_________")
            time.sleep(3)

if __name__ == "__main__":
    main()

import socket
import re
import time

USER_COOKIE = "user=9320c05a78627ad649cc421c79d34a6e"
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

def get_html_code(request):
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((HOST, PORT))
                sock.sendall(request)

                chunks = []
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                response_bytes = b"".join(chunks)

            response_str = response_bytes.decode("utf-8")
            parts = response_str.split("\r\n\r\n", 1)

            return parts[1] if len(parts) > 1 else response_str

        except (TimeoutError, socket.timeout) as e:
            print("_________")
            print("Сервер не ответил (таймаут), повторная попытка")
            print("_________")
            time.sleep(3)

def create_request(method, path, query_params=None, headers=None, cookies=None, form_data=None, file_data=None):
    params_str = "?" + "&".join(f"{key}={value}" for key, value in query_params.items()) if query_params else ""
    path = path + params_str

    actual_method = method.upper()
    if actual_method == "LINK":
        actual_method = "GET"
    elif actual_method == "FILE":
        actual_method = "POST"
    start_line = f"{actual_method} {path} HTTP/1.1\r\n"

    all_headers = {"Host": HOST, "Connection": "close"}

    cookie_parts = [USER_COOKIE]
    if cookies:
        cookie_parts.extend(f"{key}={value}" for key, value in cookies.items())
    all_headers["Cookie"] = "; ".join(cookie_parts)

    if headers:
        all_headers.update(headers)
    request_body = b""

    if method == "POST":
        body_str = "&".join(f"{key}={value}" for key, value in form_data.items()) if form_data else ""
        request_body = body_str.encode('utf-8')
        all_headers["Content-Type"] = "application/x-www-form-urlencoded"

    elif method == "FILE":
        boundary = "----MyBoundaryXYZ"
        all_headers["Content-Type"] = f"multipart/form-data; boundary={boundary}"
        parts = []
        for name, content in file_data.items():
            part = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="files[]"; filename="{name}"\r\n'
                f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
                f"{content}\r\n"
            )
            parts.append(part.encode('utf-8'))
        parts.append(f"--{boundary}--\r\n".encode('utf-8'))
        request_body = b"".join(parts)

    if request_body:
        all_headers["Content-Length"] = str(len(request_body))

    request_headers = "\r\n".join(f"{key}: {value}" for key, value in all_headers.items()) + "\r\n"
    request = start_line.encode("utf-8") + request_headers.encode("utf-8") + b"\r\n" + request_body
    return request


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
        print(f"Запрос: {current_method} к {current_path}")
        request = create_request(current_method, current_path, parsed_data["query_params"], parsed_data["headers"],
                                 parsed_data["cookies"], parsed_data["form_data"], parsed_data["files"])
        html_code = get_html_code(request)
        current_method, current_path, parsed_data = parse_html_page(html_code)

        if current_method == "DONE":
            print("=========")
            print("КВЕСТ ПРОЙДЕН!")
            print(f"Секретный ключ: {current_path}")
            print("=========")
            break

        print(f"Успешно обработано {parsed_data}")
        print("********")

if __name__ == "__main__":
    main()

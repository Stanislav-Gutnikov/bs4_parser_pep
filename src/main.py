from urllib.parse import urljoin
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests_cache
import re
import logging

from configs import configure_argument_parser, configure_logging
from constants import BASE_DIR, MAIN_DOC_URL, PEP_URL
from outputs import control_output
from utils import get_response, find_tag


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    li = div.find_all('li', attrs={'class': 'toctree-l1'})
    result = [('Ссылка на статью', 'Заголовок', 'Редактор, Автор')]
    for section in tqdm(li):
        version_a_tag = find_tag(section, 'a')
        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)
        response = get_response(session, version_link)
        if response is None:
            continue
        soup = BeautifulSoup(response.text, features='lxml')
        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')
        result.append((version_link, h1.text, dl_text))

    return result


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    div_tag = soup.find_tag('div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = div_tag.find_all('ul')
    for ul_tag in ul_tags:
        if 'All versions' in ul_tag.text:
            a_tags = ul_tag.find_all('a')
            break
        else:
            raise Exception('empty')
    results = [('Ссылка на документацию', 'Версия', 'Статус')]
    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        try:
            research = re.search(pattern, a_tag.text)
            version = research.group(1)
            status = research.group(2)
        except Exception('Ничего не нашлось'):
            version = link
            status = ''
        results.append((link, version, status))

    return results


def pep(session):
    response = get_response(session, PEP_URL)
    soup = BeautifulSoup(response.text, 'lxml')
    num_idx_table = soup.find('section', attrs={'id': 'numerical-index'})
    tr_tags = num_idx_table.find_all('tr')
    statuses = {
        'A': 0,
        'D': 0,
        'F': 0,
        'P': 0,
        'R': 0,
        'S': 0,
        'W': 0,
        '': 0,
    }
    for tag in tr_tags:
        preview_status = tag.find('abbr')
        pep = tag.find('a')
        if pep is not None and preview_status is not None:
            link = urljoin(PEP_URL, pep['href'])
            response = get_response(session, link)
            soup = BeautifulSoup(response.text, 'lxml')
            dd_tag = soup.find('dd', attrs={'class': 'field-even'})
            status = dd_tag.find('abbr')
            try:
                if preview_status.text[-1] == status.text[0]:
                    statuses[status.text[0]] += 1
            except Exception:
                statuses[''] += 1
                logging.exception(
                        'Возникла ошибка статуса PEP',
                        stack_info=True
                    )
    results = []
    for key, val in statuses.items():
        results.append((key, val))
    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = get_response(session, downloads_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    table_tag = find_tag(soup, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(table_tag, 'a', attrs={
        'href': re.compile(r'.+pdf-a4\.zip$')
        })
    pdf_a4_link = pdf_a4_tag['href']
    file_url = urljoin(downloads_url, pdf_a4_link)
    filename = file_url.split('/')[-1]
    download_dir = BASE_DIR / 'downloads'
    download_dir.mkdir(exist_ok=True)
    file_path = download_dir / filename
    response = session.get(file_url)
    with open(file_path, 'wb') as file_:
        file_.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {file_path}')


MODE_TO_FUNCTION = {
    'whats-new': whats_new,
    'latest-versions': latest_versions,
    'download': download,
    'pep': pep
}


def main():
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)


if __name__ == '__main__':
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки: {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parser_mode = args.mode
    results = MODE_TO_FUNCTION[parser_mode](session)
    if results is not None:
        control_output(results, args)
    logging.info('Парсер завершил работу.')

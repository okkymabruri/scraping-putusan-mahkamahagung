"""
author: Okky Mabruri
maintainer: Okky Mabruri <okkymbrur@gmail.com>
"""

import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
import io
import urllib
from pdfminer import high_level
import ssl
import time
import os
from requests.models import Response
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import date, datetime
import utils
import argparse


def get_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Putusan Mahkamah Agung Scraper", add_help=True
    )
    parser.add_argument(
        "-k",
        "--keyword",
        required=True,
        dest="keyword",
        help="Masukkan keyword pencarian putusan mahkamah agung",
    )

    return parser.parse_args(argv)


def open_page(link):
    count = 0
    while count < 3:
        try:
            return BeautifulSoup(requests.get(link).text, "lxml")
        except:
            count += 1
            time.sleep(5)


def get_detail(soup, keyword):
    try:
        text = (
            soup.find(lambda tag: tag.name == "td" and keyword in tag.text)
            .find_next()
            .get_text()
            .strip()
        )
        return text
    except:
        return ""


def get_pdf(url, path_pdf):
    # ctx = ssl.create_default_context()
    # ctx.check_hostname = False
    # ctx.verify_mode = ssl.CERT_NONE
    # file = urllib.request.urlopen(url), context=ctx).read()
    file = urllib.request.urlopen(url)
    file_name = file.info().get_filename().replace("/", " ")
    with file, open(f"{path_pdf}/{file_name}", "wb") as out_file:
        file = file.read()
        out_file.write(file)

    return io.BytesIO(file), file_name


def clean_text(text):
    text = text.replace("M a h ka m a h A g u n g R e p u blik In d o n esia\n", "")
    text = text.replace("Disclaimer\n", "")
    text = text.replace(
        "Kepaniteraan Mahkamah Agung Republik Indonesia berusaha untuk selalu mencantumkan informasi paling kini dan akurat sebagai bentuk komitmen Mahkamah Agung untuk pelayanan publik, transparansi dan akuntabilitas\n",
        "",
    )
    text = text.replace(
        "pelaksanaan fungsi peradilan. Namun dalam hal-hal tertentu masih dimungkinkan terjadi permasalahan teknis terkait dengan akurasi dan keterkinian informasi yang kami sajikan, hal mana akan terus kami perbaiki dari waktu kewaktu.\n",
        "",
    )
    text = text.replace(
        "Dalam hal Anda menemukan inakurasi informasi yang termuat pada situs ini atau informasi yang seharusnya ada, namun belum tersedia, maka harap segera hubungi Kepaniteraan Mahkamah Agung RI melalui :\n",
        "",
    )
    text = text.replace(
        "Email : kepaniteraan@mahkamahagung.go.id    Telp : 021-384 3348 (ext.318)\n",
        "",
    )
    return text


def extract_data(link, keyword, path_output, path_pdf):
    soup = open_page(link)
    table = soup.find("table", {"class": "table"})
    judul = table.find("h2").text
    soup.find("table", {"class": "table"}).find("h2").decompose()

    nomor = get_detail(table, "Nomor")
    tingkat_proses = get_detail(table, "Tingkat Proses")
    klasifikasi = get_detail(table, "Klasifikasi")
    kata_kunci = get_detail(table, "Kata Kunci")
    tahun = get_detail(table, "Tahun")
    tanggal_register = get_detail(table, "Tanggal Register")
    lembaga_peradilan = get_detail(table, "Lembaga Peradilan")
    jenis_lembaga_peradilan = get_detail(table, "Jenis Lembaga Peradilan")
    hakim_ketua = get_detail(table, "Hakim Ketua")
    hakim_anggota = get_detail(table, "Hakim Anggota")
    panitera = get_detail(table, "Panitera")
    amar = get_detail(table, "Amar")
    amar_lainnya = get_detail(table, "Amar Lainnya")
    catatan_amar = get_detail(table, "Catatan Amar")
    tanggal_musyawarah = get_detail(table, "Tanggal Musyawarah")
    tanggal_dibacakan = get_detail(table, "Tanggal Dibacakan")
    kaidah = get_detail(table, "Kaidah")
    abstrak = get_detail(table, "Abstrak")

    try:
        link_pdf = soup.find("a", href=re.compile(r"/pdf/"))["href"]
        file_pdf, file_name_pdf = get_pdf(link_pdf, path_pdf)
        text_pdf = high_level.extract_text(file_pdf)
        text_pdf = clean_text(text_pdf)
    except:
        link_pdf = ""
        text_pdf = ""
        file_name_pdf = ""

    data = [
        judul,
        nomor,
        tingkat_proses,
        klasifikasi,
        kata_kunci,
        tahun,
        tanggal_register,
        lembaga_peradilan,
        jenis_lembaga_peradilan,
        hakim_ketua,
        hakim_anggota,
        panitera,
        amar,
        amar_lainnya,
        catatan_amar,
        tanggal_musyawarah,
        tanggal_dibacakan,
        kaidah,
        abstrak,
        link,
        link_pdf,
        file_name_pdf,
        text_pdf,
    ]
    result = pd.DataFrame(
        [data],
        columns=[
            "judul",
            "nomor",
            "tingkat_proses",
            "klasifikasi",
            "kata_kunci",
            "tahun",
            "tanggal_register",
            "lembaga_peradilan",
            "jenis_lembaga_peradilan",
            "hakim_ketua",
            "hakim_anggota",
            "panitera",
            "amar",
            "amar_lainnya",
            "catatan_amar",
            "tanggal_musyawarah",
            "tanggal_dibacakan",
            "kaidah",
            "abstrak",
            "link",
            "link_pdf",
            "file_name_pdf",
            "text_pdf",
        ],
    )

    keyword = keyword.replace("/", " ")

    destination = (
        f'{path_output}/putusan_ma_{keyword}_{date.today().strftime("%Y-%m-%d")}'
    )
    if not os.path.isfile(f"{destination}.csv"):
        result.to_csv(f"{destination}.csv", header=True, index=False)
    else:
        result.to_csv(f"{destination}.csv", mode="a", header=False, index=False)


def run_process(keyword, page, path_output, path_pdf):
    link = f"https://putusan3.mahkamahagung.go.id/search.html?q={keyword}&page={page}"
    print(link)

    soup = open_page(link)
    links = soup.find_all("a", {"href": re.compile("/direktori/putusan")})

    for link in links:
        extract_data(link["href"], keyword, path_output,path_pdf)


if __name__ == "__main__":
    args = get_args()
    keyword = args.keyword
    # keyword = "Pdt.Sus-BPSK"
    path_output = utils.create_path("putusan")
    path_pdf = utils.create_path("pdf-putusan")

    link = f"https://putusan3.mahkamahagung.go.id/search.html?q={keyword}&page=1"

    soup = open_page(link)

    total_data = re.search(
        "Ditemukan ([0-9]+) data",
        soup.find("div", {"class": "col-md-7"}).get_text().strip(),
    ).group(1)

    last_page = int(soup.find_all("a", {"class": "page-link"})[-1].get(
        "data-ci-pagination-page"
    ))

    print(f"Scraping with keyword: {keyword} - {total_data} data - {last_page} page")

    futures = []
    with ThreadPoolExecutor() as executor:
        for page in range(last_page):
            futures.append(
                executor.submit(run_process, keyword, page + 1, path_output, path_pdf)
            )
    wait(futures)
"""_summary_

    Returns:
        _type_: _description_
"""

import collections
import argparse

import os
from pathlib import Path

from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdfinterp import PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import resolve1
from pdfminer.layout import LAParams, LTTextBox

from tqdm import tqdm


os.chdir(os.path.dirname(__file__))


def get_parser():
    """Configuration de argparse pour les options de ligne de commandes"""
    parser = argparse.ArgumentParser(
        prog=f"python {Path(__file__).name}",
        description="Comparaison des performances entre deux requêtes SQL. Ajoute implicitement et automatiquement une commande EXPLAIN.",  # pylint: disable=line-too-long
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--page",
        "-p",
        action="store",
        default=0,
        type=int,
        help="indique la page que l'on veut transformer",
    )
    parser.add_argument(
        "--output",
        "-o",
        action="store",
        default="output.csv",
        help="indique le nom du fichier de sortie",
    )
    parser.add_argument(
        "--filename",
        "-f",
        action="store",
        default="hienghene-Fr.pdf",
        help="indique le nom du pdf d'entré",
    )
    parser.add_argument(
        "--aprox_x",
        "-ax",
        action="store",
        default=70,
        type=int,
        help="aproximation en largeur",
    )
    parser.add_argument(
        "--aprox_y",
        "-ay",
        action="store",
        default=10,
        type=int,
        help="aproximation en heauteur",
    )
    parser.add_argument("--show", action="store_true")

    return parser


list_column = []


def reassemble_text(tupple_liste):  # pylint: disable=missing-function-docstring
    def my_sort(element):
        return (round(element[1]), round(element[0]))

    tupple_liste.sort(key=my_sort)
    res = ""
    for tupple in tupple_liste:

        res += tupple[2]
    return res


def transform_dict_to_str(dico, aprox):  # pylint: disable=missing-function-docstring

    res = ""
    current = 0
    for dico_element in dico:
        empty_space = list_column.index(aproximatif(list_column, dico_element, aprox))
        if empty_space > current:
            for _ in range(0, empty_space - current):
                res += ";"
                current += 1
        res += (
            reassemble_text(dico[dico_element])
            .replace("\n", "")
            .replace("  ", " ")
            .replace(";", ")")
            + ";"
        )
        current += 1
    return res[0 : len(res) - 1]


def dico_to_csv(
    dico, file, aprox, num_page
):  # pylint: disable=missing-function-docstring

    dico = collections.OrderedDict(sorted(dico.items(), reverse=True))
    for index in dico:
        dico[index] = collections.OrderedDict(sorted(dico[index].items()))
    for index in dico:
        if (
            len(dico[index]) > 2
            and aproximatif(list_column, list(dico[index])[0], aprox) == list_column[0]
        ):
            file.write(
                transform_dict_to_str(dico[index], aprox) + ";" + str(num_page) + "\n"
            )


def add_list(val, approx):  # pylint: disable=missing-function-docstring

    if not aproximatif(list_column, val, approx) in list_column:
        list_column.append(val)
        list_column.sort()


def aproximatif(
    collection, test_y, degres_aprox=10
):  # pylint: disable=missing-function-docstring

    for key in collection:
        if key - degres_aprox < test_y < key + degres_aprox:
            return key
    return test_y


def page_to_csv(
    page, file, aprox_y, aprox_x, num_page
):  # pylint: disable=missing-function-docstring

    global list_column
    list_column = []
    interpreter.process_page(page)
    layout = device.get_result()
    dico = {}
    for lobj in layout:
        if isinstance(lobj, LTTextBox):
            coord_x, coord_x_prime, coord_y, coord_y_prime, text = (
                lobj.bbox[0],
                lobj.bbox[2],
                lobj.bbox[3],
                lobj.bbox[1],
                lobj.get_text(),
            )
            key_y = aproximatif(dico, coord_y, aprox_y)
            add_list(coord_x, aprox_x)
            # todo defaultdict
            if not key_y in dico:
                dico[key_y] = {}
            key_x = aproximatif(dico[key_y], coord_x, aprox_x)
            if key_x in dico[key_y]:
                dico[key_y][key_x].append((coord_x, coord_y, text))
            else:
                dico[key_y][key_x] = [(coord_x, coord_y, text)]
    dico_to_csv(dico, file, aprox_x, num_page)


if __name__ == "__main__":
    args = get_parser().parse_args()
    file_input = "pdf/" + args.filename
    with open(file_input, "rb") as pdf_file:
        rsrcmgr = PDFResourceManager()
        laparams = LAParams()
        device = PDFPageAggregator(rsrcmgr, laparams=laparams)
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pages = PDFPage.get_pages(pdf_file)

        parser_pdf = PDFParser(pdf_file)
        document = PDFDocument(parser_pdf)
        # This will give you the count of pages
        nb_pages = resolve1(document.catalog["Pages"])["Count"]
        START = 64
        END = 252
        i = 1

        numero_page = args.page
        file_output = "output/" + args.output
        if numero_page == 0:
            with tqdm(total=nb_pages - 1 - (nb_pages - END) - START) as pbar:
                with open(file_output, "w", encoding="utf-8") as file:
                    for page_pdf in pages:
                        if START <= i <= END:
                            page_to_csv(
                                page_pdf,
                                file,
                                args.aprox_y,
                                args.aprox_x,
                                i,
                            )
                            pbar.update()
                        i += 1
        else:
            if 0 <= numero_page < nb_pages:
                with open(file_output, "w", encoding="utf-8") as file:
                    for page_pdf in pages:
                        if i == numero_page:
                            page_to_csv(
                                page_pdf,
                                file,
                                args.aprox_y,
                                args.aprox_x,
                                i,
                            )
                        i += 1

            else:
                print("Le numeros de page est en dehors du pdf")

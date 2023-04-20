"""_summary_

    Returns:
        _type_: _description_
"""


import argparse

import os
from pathlib import Path
import fitz  # pip install PyMuPDF

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
        default="filename-rectangle.pdf",
        help="indique le nom du fichier de sortie",
    )
    parser.add_argument(
        "--filename",
        "-f",
        action="store",
        default="hienghene-Fr.pdf",
        help="indique le nom du pdf d'entré",
    )

    return parser


def draw_rectangle(page, num_page, rectangle_pdf):

    interpreter.process_page(page)
    layout = device.get_result()
    page = rectangle_pdf.load_page(num_page - 1)
    dict_ = rectangle_pdf[num_page - 1].get_text("dict")
    # width = dict_["width"]
    height = dict_["height"]
    for lobj in layout:
        if isinstance(lobj, LTTextBox):
            coord_x, coord_x_prime, coord_y, coord_y_prime = (
                lobj.bbox[0],
                lobj.bbox[2],
                lobj.bbox[3],
                lobj.bbox[1],
            )

            rectangle_pdf[num_page - 1].draw_rect(
                [
                    coord_x,
                    height - coord_y,
                    coord_x_prime,
                    height - coord_y_prime,
                ],
                color=(0, 0, 1),
                width=1,
            )


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
        i = 1

        numero_page = args.page
        file_output = args.output
        if args.output == "filename-rectangle.pdf":
            tmp = args.filename.split(".")
            file_output = "output/" + ".".join(tmp[0 : len(tmp) - 1]) + "-rectangle.pdf"
        if numero_page == 0:
            with tqdm(total=nb_pages) as pbar:
                with fitz.open(file_input) as rectangle_pdf:
                    for page_pdf in pages:
                        draw_rectangle(
                            page_pdf,
                            i,
                            rectangle_pdf=rectangle_pdf,
                        )
                        pbar.update()
                        i += 1
                    rectangle_pdf.save(file_output)
        else:
            if 0 <= numero_page < nb_pages:
                with fitz.open(file_input) as rectangle_pdf:
                    for page_pdf in pages:
                        if i == numero_page:
                            draw_rectangle(
                                page_pdf,
                                i,
                                rectangle_pdf=rectangle_pdf,
                            )
                        i += 1
                    rectangle_pdf.save(file_output)

            else:
                print("Le numeros de page est en dehors du pdf")

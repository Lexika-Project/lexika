import os

import argparse

import pytesseract
import fitz

import cv2
import numpy as np


from pathlib import Path
import json

from tqdm import tqdm

DELIM = "#@#"

MODIF_RECU = [
    ("- ", ""),
    ("(7)", "(T)"),
    ("(11)", "(il)"),
    ("({)", "(Y)"),
    ("(})", "(Y)"),
    ("{", "("),
    ("}", ")"),
    ("(0)", "(O)"),
    ("fT)", "(T)"),
    (";", ","),
]

LANGUE_LIST = [
    "français",
    "pije",
    "fwâi",
    "nemi",
    "temala",
    "nemi",
    "côte est",
    "jawe",
    "pige",
    "fuät",
    "fuat",
    "nemt",
    "jave",
]


def get_parser():
    """Configuration de argparse pour les options de ligne de commandes"""
    parser = argparse.ArgumentParser(
        prog=f"python {Path(__file__).name}",
        description="Transformation d'un pdf en text",  # pylint: disable=line-too-long
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--page",
        "-p",
        action="store",
        default=0,
        type=int,
        help="""indique la page que l'on veut transformer
        (si cette argument n'est pas invoquer le programme fait tout le pdf)""",
    )
    parser.add_argument(
        "--output",
        "-o",
        choices=["pdf", "img"],
        action="store",
        default="pdf",
        help="indique le type de sortie",
    )
    parser.add_argument(
        "--filename",
        "-f",
        action="store",
        default="hienghene-Fr.pdf",
        help="indique le nom du pdf d'entré",
    )
    parser.add_argument(
        "--process",
        action="store",
        choices=[*range(2), -1],
        default=0,
        type=int,
        help="""choix du programme
        (-1 : test),
        (0 : hienghene),
        (1 : nyelayu)""",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="afiche les changements effectuer",
    )

    return parser


def overlap(
    elem1, elem2, tolerence_top=0, tolerence_left=0
):  # pylint: disable=missing-function-docstring
    """
    Vérifie si deux éléments se chevauchent en considérant des tolérances de position.

    Args:
        elem1 (dict): Informations sur le premier élément.
        elem2 (dict): Informations sur le deuxième élément.
        tolerence_top (int): Tolérance pour le chevauchement vertical.
        tolerence_left (int): Tolérance pour le chevauchement horizontal.

    Returns:
        bool: True si les éléments se chevauchent, False sinon.
    """
    if (
        (elem1["top"] >= elem2["top"] + elem2["height"] + tolerence_top)
        or (elem1["top"] + elem1["height"] <= elem2["top"] - tolerence_top)
        or (elem1["left"] + elem1["width"] <= elem2["left"] - tolerence_left)
        or (elem1["left"] >= elem2["left"] + elem2["width"] + tolerence_left)
    ):
        return False
    return True


def compare(elem1, elem2, tolerence=1):  # pylint: disable=missing-function-docstring
    """
    Vérifie si deux éléments se chevauchent en considérant des tolérances de position.

    Args:
        elem1 (dict): Informations sur le premier élément.
        elem2 (dict): Informations sur le deuxième élément.
        tolerence_top (int): Tolérance pour le chevauchement vertical.
        tolerence_left (int): Tolérance pour le chevauchement horizontal.

    Returns:
        bool: True si les éléments se chevauchent, False sinon.
    """
    if elem1 is None or elem2 is None:
        return False
    if "bold" in elem1:
        if elem1["bold"] != elem2["bold"]:
            return False
    return (
        abs(elem1["top"] - elem2["top"]) < tolerence
        and abs(elem1["left"] - elem2["left"]) < tolerence
    )


def return_index_of_array(
    array, element
):  # pylint: disable=missing-function-docstring,redefined-outer-name
    """
    Retourne l'indice de l'élément dans un tableau en comparant avec une tolérance.

    Args:
        array (list): Tableau d'éléments à comparer.
        element (dict): Élément à comparer.

    Returns:
        int or None: Indice de l'élément dans le tableau ou None s'il n'est pas trouvé.
    """
    for test in array:
        if compare(test, element):
            return array.index(test)
    return None


def concat(element1, element2):  # pylint: disable=missing-function-docstring
    """
    Concatène deux éléments en un seul, en tenant compte des positions et du texte.

    Args:
        element1 (dict): Premier élément à concaténer.
        element2 (dict): Deuxième élément à concaténer.

    Returns:
        dict: Élément résultant de la concaténation.
    """
    if abs(element1["top"] - element2["top"]) > 40:
        if element1["top"] < element2["top"]:
            text = element1["text"] + " " + element2["text"]
        else:
            text = element2["text"] + " " + element1["text"]
    elif element1["left"] < element2["left"]:
        text = element1["text"] + " " + element2["text"]
    else:
        text = element2["text"] + " " + element1["text"]
    to_add = {
        "top": min(element1["top"], element2["top"]),
        "left": min(element2["left"], element1["left"]),
        "width": max(
            element1["left"] + element1["width"],
            element2["left"] + element2["width"],
        )
        - min(element1["left"], element2["left"]),
        "height": max(
            element1["top"] + element1["height"],
            element2["top"] + element2["height"],
        )
        - min(element1["top"], element2["top"]),
        "text": text,
    }
    if "bold" in element1:
        to_add["bold"] = element1["bold"] and element2["bold"]
    return to_add


def not_column_begin(elem, approx=200):
    """
    Vérifie si un élément ne débute pas une colonne.

    Args:
        elem (dict): Élément à vérifier.
        approx (int): Tolérance pour la différence de position.

    Returns:
        bool: True si l'élément ne débute pas une colonne, False sinon.
    """
    return abs(elem["left"] - COLLUMN_TO_LANGUE[get_closest_lang(elem)]) > approx


def global_compare(
    element1, element2, array, approx_top=15, approx_left=90
):  # pylint: disable=missing-function-docstring
    """
    Compare deux éléments globalement en tenant compte des positions.

    Args:
        element1 (dict): Premier élément à comparer.
        element2 (dict): Deuxième élément à comparer.
        array (list): Tableau d'éléments de référence pour la comparaison.
        approx_top (int): Tolérance pour la différence de position verticale.
        approx_left (int): Tolérance pour la différence de position horizontale.

    Returns:
        bool: True si les éléments se chevauchent selon les critères donnés, False sinon.
    """
    return (
        overlap(element1, element2, tolerence_left=100, tolerence_top=0)
        and not_column_begin(element1)
        and not_column_begin(element2)
        or (
            (
                abs(COLLUMN_TO_LANGUE["français"] - element1["left"]) < approx_left
                and abs(COLLUMN_TO_LANGUE["français"] - element2["left"]) < approx_left
            )
            and overlap(
                element1, element2, tolerence_left=approx_left, tolerence_top=approx_top
            )
        )
        or (overlap(element1, element2, tolerence_left=50, tolerence_top=0))
    )


def get_fr_column(array):  # pylint: disable=missing-function-docstring
    """
    Récupère les éléments situés dans la colonne française.

    Args:
        array (list): Tableau d'éléments à filtrer.

    Returns:
        list: Liste des éléments dans la colonne française.
    """
    res = []
    for element in array:
        if abs(element["left"] - COLLUMN_TO_LANGUE["français"]) < 400:
            res.append(element)
    return res


def get_most_close_fr(array, element):  # pylint: disable=missing-function-docstring
    """
    Obtient l'élément le plus proche dans la colonne française par rapport à un élément donné.

    Args:
        array (list): Tableau d'éléments de référence.
        element (dict): Élément de référence pour la comparaison.

    Returns:
        dict: Élément le plus proche dans la colonne française.
    """
    fr_array = get_fr_column(array)
    res = fr_array[0]
    for element_fr in fr_array:
        if abs(element_fr["top"] - element["top"]) < abs(res["top"] - element["top"]):
            res = element_fr
    return res


def fr_compare(element1, element2, array):  # pylint: disable=missing-function-docstring
    """
    Compare deux éléments en tenant compte de la position dans la colonne française.

    Args:
        element1 (dict): Premier élément à comparer.
        element2 (dict): Deuxième élément à comparer.
        array (list): Tableau d'éléments de référence pour la comparaison.

    Returns:
        bool: True si les éléments correspondent selon les critères donnés, False sinon.
    """
    element1_close = get_most_close_fr(array, element1)
    element2_close = get_most_close_fr(array, element2)
    return (
        (not compare(element1, element1_close) or not compare(element2, element2_close))
        and abs(element2["left"] - element1["left"]) < 200
        and compare(element1_close, element2_close)
    )


def old1_concat_box(array, func_compare):  # pylint: disable=missing-function-docstring
    """
    Concatène les boîtes de texte du tableau en utilisant la fonction de comparaison donnée.

    Args:
        array (list): Tableau d'éléments à concaténer.
        func_compare (function): Fonction de comparaison pour déterminer si les éléments peuvent être concaténés.

    Returns:
        list: Liste des éléments concaténés.
    """
    change = True
    while change:
        change = False
        res = []
        for element1 in array:
            if (
                not any(overlap(element1, elem2) for elem2 in res)
                and element1["top"] > TITLE_TOP
            ):
                for element2 in array:
                    if not overlap(element1, element2) and func_compare(
                        element1, element2, array
                    ):
                        change = True
                        concat(array, res, element1, element2)
            else:
                for element2 in array:
                    if overlap(element1, element2) and func_compare(
                        element1, element2, array
                    ):
                        change = True
                        concat(array, res, element1, element2)
        array = res

    return res


def get_most_close(array, test, func_compare):
    """
    Obtient l'élément le plus proche d'un élément de test par rapport à une fonction de comparaison donnée.

    Args:
        array (list): Tableau d'éléments de référence.
        test (dict): Élément de test pour la comparaison.
        func_compare (function): Fonction de comparaison.

    Returns:
        dict: Élément le plus proche du test.
    """
    res = None
    for elem in array:
        if func_compare(test, elem, array) and not compare(test, elem):
            if res is None:
                res = elem
            else:
                if abs(elem["top"] - res["top"]) < 40 or elem["left"] < res["left"]:
                    res = elem

    return res


def is_inside(elem1, elem2):
    """
    Vérifie si l'élément 1 est entièrement à l'intérieur de l'élément 2.

    Args:
        elem1 (dict): Premier élément à vérifier.
        elem2 (dict): Deuxième élément pour la vérification.

    Returns:
        bool: True si elem1 est entièrement à l'intérieur de elem2, False sinon.
    """
    return (
        elem1["top"] <= elem2["top"]
        and elem1["left"] <= elem2["left"]
        and (elem1["left"] + elem1["width"]) >= (elem2["left"] + elem2["width"])
        and (elem1["top"] + elem1["height"]) >= (elem2["top"] + elem2["height"])
    )


def concat_box(
    array, func_compare, debug, pdf_page=None, file_output_name=None, num_page=None
):  # pylint: disable=missing-function-docstring
    """
    Concatène les boîtes de texte en utilisant la fonction de comparaison donnée.

    Args:
        array (list): Tableau d'éléments à concaténer.
        func_compare (function): Fonction de comparaison pour déterminer si les éléments peuvent être concaténés.
        debug (bool): Activation du mode débogage.
        pdf_page (object): Objet de page PDF.
        file_output_name (str): Nom du fichier de sortie.
        num_page (int): Numéro de la page.

    Returns:
        list: Liste des éléments concaténés.
    """
    change = True
    the_change = ""
    tri_rapide(array, compare_sort)
    while change:
        change = False
        res = []
        if debug:
            tmp_img = pdf_page.copy()
            save_as_img(array, tmp_img, file_output_name, num_page, error=False)
            print(the_change)

            result = input(
                "Enter pour continuer ou q pour passer au prochain process:\n"
            )
            if result.lower() == "q":
                debug = False
        for element1 in array:
            if not change:
                most_close = get_most_close(array, element1, func_compare)
                if most_close is not None:
                    the_change = concat(element1, most_close)
                    res.append(the_change)
                    change = True

        for element1 in array:
            if not any(
                is_inside(tmp, element1) and tmp["bold"] == element1["bold"]
                for tmp in res
            ):
                res.append(element1)
        array = res
    return res


def get_the_min(array):  # pylint: disable=missing-function-docstring
    """
    Obtient la valeur minimale du paramètre 'left' dans le tableau.

    Args:
        array (list): Tableau d'éléments.

    Returns:
        int: Valeur minimale de la propriété 'left'.
    """
    res = 10_000
    for element in array:  # pylint: disable=redefined-outer-name
        if element["top"] > TITLE_TOP:
            res = min(res, element["left"])
    return res


def get_the_smallest_overlap(array, elem_test):
    """
    Obtient l'élément avec le plus petit recouvrement parmi les éléments du tableau.

    Args:
        array (list): Tableau d'éléments.
        elem_test (dict): Élément de test.

    Returns:
        dict: Élément avec le plus petit recouvrement par rapport à elem_test.
    """
    smallest = elem_test
    for elem in array:
        if (
            overlap(elem, elem_test)
            and elem["width"] * elem["height"] < smallest["width"] * smallest["height"]
        ):
            smallest = elem
    return smallest


def suppr_overlap(array):  # pylint: disable=missing-function-docstring
    """
    Supprime les chevauchements entre les éléments du tableau.

    Args:
        array (list): Tableau contenant les éléments à traiter.

    Returns:
        list: Tableau contenant les éléments sans chevauchement.
    """
    res = []
    change = True
    while change:
        change = False
        for element1 in array:
            if element1["top"] > TITLE_TOP:
                smallest_overlap = get_the_smallest_overlap(array, element1)
                if not any(overlap(smallest_overlap, element2) for element2 in res):
                    change = True
                    res.append(element1)
                elif not compare(smallest_overlap, element1):
                    for elem_res in res:
                        if (
                            overlap(elem_res, smallest_overlap)
                            and len(
                                list(
                                    set(
                                        smallest_overlap["text"].lower().split()
                                    ).intersection(elem_res["text"].lower().split())
                                )
                            )
                            == 0
                        ):
                            res.append(smallest_overlap)

    return res


def particionner(tab, deb, fin, func):  # pylint: disable=missing-function-docstring
    """
    Partitionne un tableau en utilisant la technique du tri rapide.

    Args:
        tab (list): Tableau à trier.
        deb (int): Indice de début de la partition.
        fin (int): Indice de fin de la partition.
        func (function): Fonction de comparaison pour le tri.

    Returns:
        None: Modifie le tableau en place.
    """
    if deb < fin:
        curent = deb
        for i in range(deb + 1, fin):
            if func(tab[curent], tab[i]) and curent < i:
                tmp = tab[curent]
                tab[curent] = tab[i]
                tab[i] = tab[curent + 1]
                tab[curent + 1] = tmp
                curent += 1
        particionner(tab, deb, curent, func)
        particionner(tab, curent + 1, fin, func)


def tri_rapide(tab, func):  # pylint: disable=missing-function-docstring
    """
    Effectue un tri rapide sur le tableau donné.

    Args:
        tab (list): Tableau à trier.
        func (function): Fonction de comparaison pour le tri.

    Returns:
        None: Modifie le tableau en place.
    """
    particionner(tab, 0, len(tab), func)


def compare_sort(elem1, elem2):  # pylint: disable=missing-function-docstring
    """
    Fonction de comparaison utilisée pour le tri rapide.

    Args:
        elem1 (dict): Premier élément à comparer.
        elem2 (dict): Deuxième élément à comparer.

    Returns:
        int: Résultat de la comparaison (0 si elem1 avant elem2, 1 sinon).
    """
    if elem1["top"] + elem1["height"] < elem2["top"]:
        return 0
    if elem2["top"] + elem2["height"] < elem1["top"]:
        return 1
    if elem1["left"] < elem2["left"]:
        return 0
    return 1


def overlap_from_two_array(
    array_base, array_clean
):  # pylint: disable=missing-function-docstring
    """
    Calcule les chevauchements entre deux tableaux d'éléments.

    Args:
        array_base (list): Tableau de base.
        array_clean (list): Tableau à nettoyer des chevauchements.

    Returns:
        list: Tableau résultant des chevauchements.
    """
    res = []
    for element_clean in array_clean:
        tmp = []
        for element_base in array_base:
            if overlap(element_clean, element_base):
                tmp.append(element_base)
        tri_rapide(tmp, compare_sort)
        # print(tmp)
        tmp_text = ""
        for text in tmp:
            tmp_text += " " + text["text"]
        for rule in MODIF_RECU:
            tmp_text = tmp_text.replace(rule[0], rule[1])
        res.append(
            {
                "top": element_clean["top"],
                "left": element_clean["left"],
                "width": element_clean["width"],
                "height": element_clean["height"],
                "text": tmp_text,
            }
        )
    return res


def from_array_to_line(array):  # pylint: disable=missing-function-docstring
    """
    Organise les éléments du tableau en lignes en fonction de la colonne 'français'.

    Args:
        array (list): Tableau d'éléments.

    Returns:
        dict: Dictionnaire avec les tops des éléments comme clés et les éléments associés comme valeurs.
    """
    fr_col = get_fr_column(array)
    res = {}
    for fr_elem in fr_col:
        res[fr_elem["top"]] = []
    for elem in array:
        fr_ref = get_most_close_fr(array, elem)
        res[fr_ref["top"]].append(elem)
    return res


def get_closest_lang(elem):  # pylint: disable=missing-function-docstring
    """
    Détermine la langue la plus proche pour un élément donné.

    Args:
        elem (dict): Élément à traiter.

    Returns:
        str: Langue la plus proche de l'élément.
    """
    res = "français"
    for langue in COLLUMN_TO_LANGUE:
        # print(elem["left"])
        # print(COLLUMN_TO_LANGUE[langue])
        if abs(elem["left"] - COLLUMN_TO_LANGUE[langue]) < abs(
            elem["left"] - COLLUMN_TO_LANGUE[res]
        ):
            res = langue
    if res == "français_tab":
        return "français"
    return res


def from_line_to_csv(array):  # pylint: disable=missing-function-docstring
    """
    Convertit les éléments regroupés en lignes en une chaîne CSV.

    Args:
        array (dict): Dictionnaire avec les tops comme clés et les éléments comme valeurs.

    Returns:
        str: Chaîne CSV des éléments.
    """
    res = ""
    tmp = {}
    for elem in array:
        # print(array)
        lang = get_closest_lang(elem)
        elem["langue"] = lang
        error = False
        if lang in tmp:
            tmp[lang]["text"] += " " + elem["text"]
            error = True
        else:
            tmp[lang] = elem
        tmp[lang]["error"] = error
    if len(tmp) > 1:
        for _, elem in tmp.items():
            res += (
                elem["langue"]
                + DELIM
                + " ".join(elem["text"].split())
                + DELIM
                + str(elem["error"])
                + DELIM
                + str(elem["top"])
                + DELIM
                + str(elem["left"])
                + DELIM
                + str(elem["width"])
                + DELIM
                + str(elem["height"])
                + ";"
            )
        return res[0 : len(res) - 1]
    else:
        return ""


def find_title_coord(array):  # pylint: disable=missing-function-docstring
    """
    Cette fonction trouve et calcule les coordonnées du titre dans le tableau donné.

    Args:
        array (list): Liste d'éléments contenant les coordonnées des zones de texte.

    Returns:
        float: La coordonnée verticale calculée du titre.
    """
    tmp = []
    for elem in array:
        if len(list(set(elem["text"].lower().split()).intersection(LANGUE_LIST))) != 0:
            tmp.append(elem)
    if len(tmp) == 0:
        return 0
    tmp_res = 9999999999999999
    for elem in tmp:
        if elem["top"] < tmp_res:
            tmp_res = elem["top"]
    res = 0
    count = 0
    for elem in tmp:
        if abs(elem["top"] - tmp_res) < 50:
            res += elem["top"]
            count += 1
    return res / count


def get_title_list(array):  # pylint: disable=missing-function-docstring
    """
    Cette fonction extrait la liste des éléments considérés comme des titres du tableau donné.

    Args:
        array (list): Liste d'éléments contenant les coordonnées des zones de texte.

    Returns:
        list: Liste des éléments considérés comme des titres, triés par la coordonnée horizontale.
    """
    tmp = []
    for elem in array:
        if abs(elem["top"] - (TITLE_TOP - 50)) < 30:
            if not any(overlap(elem, elem2, tolerence_left=300) for elem2 in tmp):
                tmp.append(elem)
    res = []
    for elem in tmp:
        res.append(elem)
    res = sorted(res, key=lambda x: x["left"])
    return res


def get_array_tess(pdf_img, test_bold=False, bold_aprox=0.001):
    """
    Cette fonction utilise Tesseract pour extraire du texte et les coordonnées de boîtes englobantes à partir d'une image.

    Args:
        pdf_img (fitz.Pixmap): Image à partir de laquelle extraire le texte.
        test_bold (bool, optional): Indique s'il faut tester si le texte est en gras. Par défaut False.
        bold_aprox (float, optional): Approximation pour déterminer si le texte est en gras. Par défaut 0.001.

    Returns:
        tuple: Tuple contenant la liste des boîtes englobantes et l'image, ainsi que les dimensions de l'image (hauteur, largeur).
    """
    mat = fitz.Matrix(6, 6)
    pix = pdf_img.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    img_height, img_width, _ = img.shape
    if test_bold:
        kernel = np.ones((8, 8), np.floating)
        only_bold = cv2.dilate(img, kernel, iterations=1)
    pytesseract.pytesseract.tesseract_cmd = r"lib\Tesseract-OCR\tesseract"

    dict_ocr = pytesseract.image_to_data(
        img,
        output_type=pytesseract.Output.DICT,
        config="--psm 12 -l fra",
    )

    array_boxe = []

    for i in range(len(dict_ocr["text"])):
        if not dict_ocr["text"][i] == "":
            my_dict = {
                "top": int(dict_ocr["top"][i]),
                "left": int(dict_ocr["left"][i]),
                "width": int(dict_ocr["width"][i]),
                "height": int(dict_ocr["height"][i]),
                "text": dict_ocr["text"][i],
            }
            if test_bold:
                sub_img = only_bold[
                    my_dict["top"] : my_dict["top"] + my_dict["height"],
                    my_dict["left"] : my_dict["left"] + my_dict["width"],
                ]
                percent_black_pixel = np.sum(sub_img < 50) / sub_img.size
                my_dict["bold_percent"] = percent_black_pixel
                if my_dict["bold_percent"] > bold_aprox:
                    my_dict["bold"] = True
                else:
                    my_dict["bold"] = False
            else:
                my_dict["bold"] = False
            array_boxe.append(my_dict)
    return (array_boxe, img, img_height, img_width)


def save_as_img(array, img, file_output_name, num_page, color=(255, 0, 0), error=True):
    """
    Sauvegarde l'image avec les boîtes englobantes autour des éléments dans la liste.

    Args:
        array (list): Liste des éléments avec les coordonnées des boîtes englobantes.
        img (numpy.ndarray): Image sur laquelle dessiner les boîtes englobantes.
        file_output_name (str): Nom du fichier de sortie.
        num_page (int): Numéro de la page.
        color (tuple, optional): Couleur des boîtes englobantes. Par défaut (255, 0, 0) (rouge).
        error (bool, optional): Indique s'il faut marquer en bleu les boîtes sans texte. Par défaut True.
    """
    for element in array:
        if "bold" in element:
            if element["bold"]:
                final_color = (0, 170, 0)
            elif get_most_close_bold(array, element) is None and error:
                final_color = (0, 0, 170)
            else:
                final_color = (255, 0, 0)
        else:
            final_color = color
        img = cv2.rectangle(
            img,
            (
                element["left"],
                element["top"],
                element["width"],
                element["height"],
            ),
            final_color,
            4,
        )
    cv2.imwrite(
        file_output_name + ".jpg",
        img,
    )


def draw_pdf(
    array,
    pdf_page,
    num_page,
    img_width,
    img_height,
    color=(0, 0, 1),
    width=1,
    mode="normal",
):
    """
    Dessine les boîtes englobantes sur la page PDF.

    Args:
        array (list): Liste des éléments avec les coordonnées des boîtes englobantes.
        pdf_page (fitz.fitz.Page): Page PDF sur laquelle dessiner les boîtes englobantes.
        num_page (int): Numéro de la page.
        img_width (int): Largeur de l'image.
        img_height (int): Hauteur de l'image.
        color (tuple, optional): Couleur des boîtes englobantes. Par défaut (0, 0, 1) (bleu).
        width (int, optional): Largeur de la ligne de la boîte. Par défaut 1.
        mode (str, optional): Mode de dessin (non utilisé ici). Par défaut "normal".
    """
    if not pdf_page.is_wrapped:
        pdf_page.wrap_contents()

    pdf_output_width = pdf_page.rect.width
    pdf_output_height = pdf_page.rect.height
    for element in array:
        if "bold" in element:
            if element["bold"]:
                final_color = (0, 0.8, 0)
            elif get_most_close_bold(array, element) is None:
                final_color = (0.8, 0, 0)
            else:
                final_color = (0, 0, 1)
        else:
            final_color = color
        pdf_page.draw_rect(
            [
                (element["left"] * pdf_output_width) / img_width,
                (element["top"] * pdf_output_height) / img_height,
                ((element["left"] * pdf_output_width) / img_width)
                + ((element["width"] * pdf_output_width) / img_width),
                ((element["top"] * pdf_output_height) / img_height)
                + ((element["height"] * pdf_output_height) / img_height),
            ],
            color=final_color,
            width=width,
        )


def concat_horizon(elem1, elem2, array):
    """
    Vérifie si deux éléments peuvent être concaténés horizontalement.

    Args:
        elem1 (dict): Premier élément.
        elem2 (dict): Deuxième élément.
        array (list): Liste des éléments.

    Returns:
        bool: True si les éléments peuvent être concaténés horizontalement, False sinon.
    """
    return abs((elem1["left"] + elem1["width"]) - elem2["left"]) < 0


def concat_bold(elem1, elem2, array):
    """
    Vérifie si deux éléments en gras peuvent être concaténés.

    Args:
        elem1 (dict): Premier élément.
        elem2 (dict): Deuxième élément.
        array (list): Liste des éléments.

    Returns:
        bool: True si les éléments en gras peuvent être concaténés, False sinon.
    """
    return (
        elem1["bold"]
        and elem2["bold"]
        and (
            abs((elem1["left"] + elem1["width"]) - elem2["left"]) < 70
            or abs((elem2["left"] + elem2["width"]) - elem1["left"]) < 70
        )
        and abs(elem1["top"] - elem2["top"]) < 50
    )


def concat_not_bold(elem1, elem2, array):
    """
    Vérifie si deux éléments non en gras peuvent être concaténés.

    Args:
        elem1 (dict): Premier élément.
        elem2 (dict): Deuxième élément.
        array (list): Liste des éléments.

    Returns:
        bool: True si les éléments non en gras peuvent être concaténés, False sinon.
    """
    if elem1["bold"] or elem2["bold"]:
        return False
    return overlap(elem1, elem2, tolerence_left=100)


def concat_by_closest_bold(elem1, elem2, array):
    """
    Vérifie si deux éléments peuvent être concaténés en se basant sur les éléments les plus proches en gras.

    Args:
        elem1 (dict): Premier élément.
        elem2 (dict): Deuxième élément.
        array (list): Liste des éléments.

    Returns:
        bool: True si les éléments peuvent être concaténés, False sinon.
    """
    if elem1["bold"] or elem2["bold"]:
        return False
    elem1_bold = get_most_close_bold(array, elem1)
    elem2_bold = get_most_close_bold(array, elem2)
    res = compare(elem1_bold, elem2_bold) and (
        (
            abs(elem1["top"] - elem2["top"]) < 100
            or abs(elem1["left"] - elem2["left"]) < 200
        )
    )
    return res


def concat_false(elem1, elem2, array):
    return False


def suppr_middle_bold(array):
    """
    Supprime les éléments en gras dans la partie médiane d'une colonne.

    Args:
        array (list): Liste des éléments.

    Modifie:
        array (list): Modifie la liste en supprimant les éléments en gras dans la partie médiane.

    Returns:
        None
    """
    res = []
    for elem in array:
        to_add = True
        tmp_array = []
        if elem["bold"]:
            for tmp in res:
                if abs(elem["left"] - tmp[0]) < 100:
                    tmp_array.append(((tmp[0] + elem["left"]) / 2, tmp[1] + 1))
                    to_add = False
                else:
                    tmp_array.append(tmp)
            res = tmp_array
            if to_add:
                res.append((elem["left"], 1))
    delete_array = []
    for tmp in res:
        if tmp[1] < 10:
            delete_array.append(tmp[0])
    for elem in array:
        if elem["bold"] and any(abs(elem["left"] - tmp) < 100 for tmp in delete_array):
            elem["bold"] = False


def get_most_close_bold(array, test):
    """
    Retourne l'élément en gras le plus proche du test.

    Args:
        array (list): Liste des éléments.
        test (dict): Élément à tester.

    Returns:
        dict: L'élément en gras le plus proche ou None s'il n'y en a pas.
    """
    res = None
    for elem in array:
        if elem["bold"] and (
            overlap(elem, test, tolerence_left=75)
            or (test["top"] > elem["top"] and abs(elem["left"] - test["left"]) < 150)
        ):
            if res is None or elem["top"] > res["top"]:
                res = elem
    return res


def get_first_under_bold(array, test):
    """
    Retourne le premier élément en gras en dessous du test.

    Args:
        array (list): Liste des éléments.
        test (dict): Élément à tester.

    Returns:
        dict: Le premier élément en gras en dessous du test ou None s'il n'y en a pas.
    """
    res = None
    for elem in array:
        if elem["bold"]:
            if elem["top"] > test["top"] and abs(elem["left"] - test["left"] < 300):
                if res is None or elem["top"] < res["top"]:
                    res = elem
    return res


def single_language_array_to_line(array):
    """
    Fusionne les éléments du même langage dans une ligne.

    Args:
        array (list): Liste des éléments.

    Returns:
        list: Liste des lignes de texte fusionnées par langage.
    """
    tmp = {}
    for elem in array:
        if not elem["bold"]:
            bold = get_most_close_bold(array, elem)
            if bold is not None:
                key = str(bold["top"]) + "x" + str(bold["left"])
                if key in tmp:
                    tmp[key] = concat(tmp[key], elem)
                else:
                    tmp[key] = elem
    res = []
    for elem in array:
        if elem["bold"]:
            key = str(elem["top"]) + "x" + str(elem["left"])
            text = ""
            if key in tmp:
                text = tmp[key]["text"]
            res.append(elem["text"].replace(";", ",") + ";" + text.replace(";", ","))
    return res


def nyelayu_compare(elem1, elem2):
    """
    Compare deux éléments pour le langage nyelayu.

    Args:
        elem1 (dict): Premier élément.
        elem2 (dict): Deuxième élément.

    Returns:
        int: 0 si elem1 est à gauche de elem2, 1 sinon.
    """
    if elem1["left"] < 1000 < elem2["left"]:
        return 0
    if elem2["left"] < 1000 < elem1["left"]:
        return 1
    if elem1["top"] < elem2["top"]:
        return 0
    return 1


def concat_single_bold(elem1, elem2, array):
    """
    Fusionne deux éléments en conservant le style bold.

    Args:
        elem1 (dict): Premier élément.
        elem2 (dict): Deuxième élément.
        array (list): Liste des éléments.

    Returns:
        bool: True si la fusion a réussi tout en conservant le style bold, False sinon.
    """
    if not elem1["bold"] or not elem2["bold"]:
        return False
    elem1_verif = False
    elem2_verif = False

    for elem in array:
        if (
            not elem1_verif
            and not elem["bold"]
            and compare(elem1, get_most_close_bold(array, elem))
        ):
            elem1_verif = True
    for elem in array:
        if (
            not elem2_verif
            and not elem["bold"]
            and compare(elem2, get_most_close_bold(array, elem))
        ):
            elem2_verif = True
    res = False
    if not elem1_verif:
        res = compare(elem2, get_first_under_bold(array, elem1))
    if not elem2_verif:
        res = compare(elem1, get_first_under_bold(array, elem2))
    return res


def hienghene(
    pdf_img, file_output_name, csv, output_type, debug, num_page=0
):  # pylint: disable=missing-function-docstring
    """
    Traitement spécifique pour le cas de Hienghène.

    Args:
        pdf_img (object): Image du PDF.
        file_output_name (str): Nom du fichier de sortie.
        csv (object): Fichier CSV pour l'enregistrement des données.
        output_type (str): Type de sortie ("img" ou autre).
        debug (bool): Activation du mode debug.
        num_page (int): Numéro de page du PDF (par défaut 0).

    Returns:
        None
    """
    array_boxe, img, img_height, img_width = get_array_tess(pdf_img)
    if len(array_boxe) > 20:
        global TITLE_TOP
        TITLE_TOP = find_title_coord(array_boxe) + 50

        min_scale = get_the_min(array_boxe)
        list_of_title = get_title_list(array_boxe)
        if len(list_of_title) != 5:
            with open("output/log.txt", "a+") as f:
                for eleme in list_of_title:
                    f.write(json.dumps(eleme) + " | ")
                f.write(str(num_page) + "\n")
        # print(TITLE_TOP - 50)
        # print(list_of_title)
        global COLLUMN_TO_LANGUE
        COLLUMN_TO_LANGUE = {
            "français": min_scale,
            "français_tab": min_scale + 200,
            "pije": list_of_title[0]["left"],
            "fwâi": list_of_title[1]["left"],
            "nemi 1 (Temala)": list_of_title[2]["left"],
            "nemi 2 (côte est)": list_of_title[3]["left"],
            "jawe": list_of_title[4]["left"],
        }
        array_boxe = suppr_overlap(array_boxe)
        array_boxe_save = array_boxe.copy()
        array_boxe = concat_box(
            array_boxe,
            global_compare,
            debug,
            pdf_page=img,
            file_output_name=file_output_name,
            num_page=num_page,
        )
        array_boxe = concat_box(
            array_boxe,
            fr_compare,
            debug,
            pdf_page=img,
            file_output_name=file_output_name,
            num_page=num_page,
        )
        array_boxe = overlap_from_two_array(
            array_base=array_boxe_save, array_clean=array_boxe
        )

        save_line_array = from_array_to_line(array_boxe)
        for element in save_line_array.items():
            min_left = min(element[1], key=lambda x: x["left"])["left"]
            min_top = min(element[1], key=lambda x: x["top"])["top"]
            max_width_elem = max(element[1], key=lambda x: x["left"] + x["width"])
            max_height_elem = max(element[1], key=lambda x: x["top"] + x["height"])
            max_width = max_width_elem["left"] + max_width_elem["width"]
            max_height = max_height_elem["top"] + max_height_elem["height"]
            tmp = []
            tmp.append(
                {
                    "top": min_top - 6,
                    "left": min_left - 6,
                    "width": max_width - min_left + 12,
                    "height": max_height - min_top + 12,
                    "bold": False,
                }
            )
            if output_type == "img":
                save_as_img(element[1], img, file_output_name, num_page)
                save_as_img(tmp, img, file_output_name, num_page)
            else:
                draw_pdf(element[1], pdf_img, num_page, img_width, img_height)
                draw_pdf(tmp, pdf_img, num_page, img_width, img_height)
            tmp = from_line_to_csv(element[1])
            if tmp != "":
                csv.write(tmp + ";" + str(num_page) + "\n")


def nyelayu(
    pdf_img, file_output_name, csv, output_type, debug, num_page=0
):  # pylint: disable=missing-function-docstring
    """
    Traitement spécifique pour le cas de Nyelayu.

    Args:
        pdf_img (object): Image du PDF.
        file_output_name (str): Nom du fichier de sortie.
        csv (object): Fichier CSV pour l'enregistrement des données.
        output_type (str): Type de sortie ("img" ou autre).
        debug (bool): Activation du mode debug.
        num_page (int): Numéro de page du PDF (par défaut 0).

    Returns:
        None
    """
    global TITLE_TOP
    TITLE_TOP = 400
    array_boxe, img, img_height, img_width = get_array_tess(pdf_img, test_bold=True)
    array_boxe = suppr_overlap(array_boxe)
    array_boxe = concat_box(
        array_boxe,
        concat_bold,
        debug,
        pdf_page=img,
        file_output_name=file_output_name,
        num_page=num_page,
    )
    suppr_middle_bold(array_boxe)
    array_boxe = concat_box(
        array_boxe,
        concat_not_bold,
        debug,
        pdf_page=img,
        file_output_name=file_output_name,
        num_page=num_page,
    )
    array_boxe = concat_box(
        array_boxe,
        concat_by_closest_bold,
        debug,
        pdf_page=img,
        file_output_name=file_output_name,
        num_page=num_page,
    )
    # array_boxe = concat_box(array_boxe, concat_single_bold)
    tri_rapide(array_boxe, nyelayu_compare)

    if output_type == "img":
        save_as_img(array_boxe, img, file_output_name, num_page)
    else:
        draw_pdf(array_boxe, pdf_img, num_page, img_width, img_height)

    res = single_language_array_to_line(array_boxe)
    for elem in res:
        csv.write(elem + ";" + str(num_page) + "\n")


def test(
    pdf_img, file_output_name, csv, output_type, num_page=0
):  # pylint: disable=missing-function-docstring
    global TITLE_TOP
    TITLE_TOP = 0


def getProcess():
    """
    Renvoie le processus et les bornes de pages en fonction de l'argument `args.process`.

    Returns:
        list: Liste contenant le processus, la page de début et la page de fin.
    """
    match args.process:
        case 0:
            process = hienghene
            START = 64
            END = 252
        case 1:
            process = nyelayu
            START = 62
            END = 176
    return [process, START, END]


if __name__ == "__main__":
    os.chdir(os.path.dirname(__file__)) # Changement du répertoire courant
    
    # Parsing des arguments
    args = get_parser().parse_args()
    filename_without_ex = os.path.splitext(args.filename)[0]
    file_input = "pdf/" + filename_without_ex
    
    # Ouverture du fichier PDF en mode lecture binaire
    with open(file_input + ".pdf", "rb") as pdf_file:
        i = 1 # Initialisation du compteur de page

        numero_page = args.page # Numéro de page spécifié par l'utilisateur

        file_output = "output/" + filename_without_ex
        if numero_page != 0:
            file_output += "-" + str(numero_page)

        # Récupération du processus et des bornes de pages    
        process, START, END = getProcess()

        # Ouverture du fichier de sortie CSV en mode écriture
        with open(file_output + ".csv", "w", encoding="utf-8") as file:
            with fitz.open(file_input + ".pdf") as pdf_file:
                if numero_page == 0:
                    with tqdm(total=END - START) as pbar:
                        # Parcours des pages du PDF
                        for page_pdf in pdf_file:
                            if START <= i <= END:
                                # Traitement de la page en utilisant le processus approprié
                                process(
                                    page_pdf,
                                    file_output + "-" + str(i),
                                    file,
                                    args.output,
                                    args.debug,
                                    i,
                                )
                                pbar.update()
                            i += 1 # Incrémentation du compteur de page
                        if args.output == "pdf":
                            pdf_file.save(file_output + ".pdf")
                elif 0 < numero_page < pdf_file.page_count:
                    # Traitement de la page spécifiée par l'utilisateur
                    process(
                        pdf_file.load_page(numero_page - 1),
                        file_output,
                        file,
                        args.output,
                        args.debug,
                        num_page=numero_page,
                    )
                    if args.output == "pdf":
                        pdf_file.save(file_output + ".pdf")
                else:
                    print("Le numeros de page est en dehors du pdf")

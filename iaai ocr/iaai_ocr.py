import pytesseract
import fitz

import cv2
import numpy as np

import csv 



def get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1):
    """
    Utilité:
        Extrait le texte d'un fichier PDF en images, effectue une reconnaissance de caractères (OCR) à l'aide de Tesseract, 
        et renvoie une liste de dictionnaires contenant les informations sur le texte extrait.
    Paramètres:
        pdf_path: Chemin du fichier PDF.
        test_bold: (Facultatif) Un booléen indiquant si vous souhaitez tester si le texte est en gras.
        bold_aprox: (Facultatif) Le pourcentage approximatif de pixels en gras pour déterminer si le texte est en gras.
    Return:
        Une liste de dictionnaires contenant les informations du texte extrait.
    """
    pdf_document = fitz.open(pdf_path)
    images = []
    is_inside_parentheses = False

    # Parcours des pages du pdf
    for page_number in range(pdf_document.page_count):
        page = pdf_document.load_page(page_number)
        image_list = page.get_images(full=True)
        # Extraire les images de la page
        for img_info in image_list:
            xref = img_info[0]
            base_image = pdf_document.extract_image(xref)
            image_bytes = base_image["image"]
            image_np = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
            images.append(image_np)

    array_boxe = []

    # Parcours de toutes les images que l'on vient d'extraire
    for image in images:
        img_height, img_width, _ = image.shape

        # Test du texte en gras
        if test_bold:
            kernel = np.ones((4, 4), np.uint8)
            only_bold = cv2.dilate(image, kernel, iterations=1)
        else:
            only_bold = image

        pytesseract.pytesseract.tesseract_cmd = r"C:/Users/Hurel Roques Tom/Desktop/Stage Lexika/ocr/lib/tesseract.exe"

        # OCR sur l'image extraite
        dict_ocr = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT,
            config="--psm 12 -l fra",
        )
        
        # Parcours des résultats de l'OCR 
        for i in range(len(dict_ocr["text"])):
            if not dict_ocr["text"][i] == "":
                my_dict = {
                    "top": int(dict_ocr["top"][i]),
                    "left": int(dict_ocr["left"][i]),
                    "width": int(dict_ocr["width"][i]),
                    "height": int(dict_ocr["height"][i]),
                    "text": dict_ocr["text"][i],
                }

                # Déterminer la colonne en fonction de la position de la boîte de texte
                if my_dict["left"] < img_width / 2:
                    my_dict["column"] = 1
                else:
                    my_dict["column"] = 2

                # Test remplacement du texte "!es" par "les"
                if my_dict["text"] == "!es":
                    my_dict["text"] = "les"

                # Calcul pourcentage de pixels en gras
                if test_bold:
                    if is_inside_parentheses:
                        my_dict["bold"] = False
                    else:
                        sub_img = only_bold[
                            my_dict["top"] : my_dict["top"] + my_dict["height"],
                            my_dict["left"] : my_dict["left"] + my_dict["width"],
                        ]
                        percent_black_pixel = np.sum(sub_img < 50) / sub_img.size
                        my_dict["bold_percent"] = percent_black_pixel
                        my_dict["bold"] = percent_black_pixel > bold_aprox
                else:
                    my_dict["bold"] = False

                # Gestion du texte entre parenthèses
                if '(' in my_dict["text"]:
                    is_inside_parentheses = True
                if ')' in my_dict["text"]:
                    is_inside_parentheses = False

                array_boxe.append(my_dict)

    return array_boxe


def order_text(result):
    """
    Utilité:
        Trie les éléments en fonction de la colonne dans laquelle ils se trouvent et renvoie deux listes séparées 
        pour chaque colonne.
    Paramètres:
        result: Liste de dictionnaires du texte extrait.
    Return:
        Deux listes séparées pour chaque colonne du texte.
    """
    column1 = []
    column2=[]
    for item in result:
        if item['column'] == 1:
            column1.append(item)
        if item['column'] == 2:
            column2.append(item)
    return column1, column2            


def txt_fr(word):
    """
    Utilité:
        Vérifie si un mot donné est présent dans un fichier texte contenant une liste de mots français. Si le mot n'est pas dans la liste 
        et que le texte est en gras, elle indique que le mot est en gras.
    Paramètres:
        word: Dictionnaire contenant les informations du mot extrait.
    """
    dico = r"C:\Users\Hurel Roques Tom\Desktop\Stage Lexika\ocr\pdf\liste.de.mots.francais.frgut.txt"
    with open(dico, "r", encoding="utf-8") as file:
        content = file.read()
    if word['text'] in content:
        word['bold'] = False
    if word['text'] not in content:
        if word['bold_percent'] < 0.0001 :
            pass
        else:
            word['bold'] = True


def array_from_txt(column):
    """
    Utilité:
        Regroupe le texte en gras et non gras en paires et renvoie une liste de paires de texte.
    Paramètres:
        column: Liste de dictionnaires du texte extrait pour une colonne donnée.
    Return:
        Une liste de paires de texte (texte en gras et non gras).
    """
    res = []
    temp = ['', '']

    # Parcours des boîtes de texte dans la colonne
    for item in column:
        # Si le texte est en gras, ajout à la première partie de la liste temporaire
        if item['bold']:
            temp[0] += (' ' + item['text'] + ' ')
        else:
            # Si le texte n'est pas en gras, ajout à la deuxième partie de la liste temporaire
            temp[1] += (' ' + item['text'] + ' ')
            # Vérifie si le mot suivant est en gras (non-gras suivi de gras)
            if item is not column[-1]:
                next_item = column[column.index(item) + 1]
                if next_item['bold']:
                    # Si c'est le cas, ajoute la liste temporaire au résultat et réinitialise temp
                    res.append([temp[0], temp[1]])
                    temp = ['', '']

    # Si des données restent dans temp, ajoute-les au résultat
    if temp[0] or temp[1]:
        res.append([temp[0], temp[1]])

    return res


def export_to_csv(data, output_file):
    """
    Utilité:
        Exporte une liste de données vers un fichier CSV.
    Paramètres:
        data: Liste de données à exporter.
        output_file: Chemin du fichier CSV de sortie.
    """
    with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        for row in data:
            writer.writerow(row)


def csv_fusion(source, destination):
    """
    Utilité:
        Fusionne le contenu d'un fichier source avec un fichier de destination.
    Paramètres:
        source: Chemin du fichier source.
        destination: Chemin du fichier de destination.
    """
    with open(source, 'r') as f1:
        new = f1.read()
    with open(destination, 'a') as f2:
        f2.write(new)


def iaai(pdf_path, pdf1, pdf2):
    """
    Utilité:
        Coordonne l'ensemble du processus de traitement pour un fichier PDF donné. Elle extrait le texte, 
        le classe en deux colonnes, vérifie si les mots sont en français et exporte les données vers deux fichiers CSV.
    Paramètres:
        pdf_path: Chemin du fichier PDF d'entrée.
        pdf1: Chemin du premier fichier CSV de sortie.
        pdf2: Chemin du deuxième fichier CSV de sortie.
    """
    array_boxes = get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1)
    column1, column2 = order_text(array_boxes)
    
    column1 = array_from_txt(column1)
    column2 = array_from_txt(column2)
    export_to_csv(column1, pdf1)
    export_to_csv(column2, pdf2)


def multi_iaai(pdf_paths, output_paths):
    """
    Utilité:
        Permet de traiter plusieurs fichiers PDF en série en utilisant la fonction iaai pour chaque PDF.
    Paramètres:
        pdf_paths: Liste des chemins des fichiers PDF à traiter.
        output_paths: Liste des chemins des fichiers de sortie pour chaque PDF.
    """
    for i in range(len(pdf_paths)):
        pdf_path = pdf_paths[i]
        output_path = output_paths[i]
        
        array_boxes = get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1)
        column1, column2 = order_text(array_boxes)
        
        column1 = array_from_txt(column1)
        column2 = array_from_txt(column2)
        
        export_to_csv(column1, output_path + "c1.csv")
        export_to_csv(column2, output_path + "c2.csv")

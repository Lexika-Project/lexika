import pytesseract
import fitz

import cv2
import numpy as np

import csv 



def get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1):
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
    column1 = []
    column2=[]
    for item in result:
        if item['column'] == 1:
            column1.append(item)
        if item['column'] == 2:
            column2.append(item)
    return column1, column2            


def txt_fr(word):
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
    with open(output_file, mode='a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        for row in data:
            writer.writerow(row)


def csv_fusion(source, destination):
    with open(source, 'r') as f1:
        new = f1.read()
    with open(destination, 'a') as f2:
        f2.write(new)


def iaai(pdf_path, pdf1, pdf2):
    array_boxes = get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1)
    column1, column2 = order_text(array_boxes)
    
    column1 = array_from_txt(column1)
    column2 = array_from_txt(column2)
    export_to_csv(column1, pdf1)
    export_to_csv(column2, pdf2)


def multi_iaai(pdf_paths, output_paths):
    for i in range(len(pdf_paths)):
        pdf_path = pdf_paths[i]
        output_path = output_paths[i]
        
        array_boxes = get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1)
        column1, column2 = order_text(array_boxes)
        
        column1 = array_from_txt(column1)
        column2 = array_from_txt(column2)
        
        export_to_csv(column1, output_path + "c1.csv")
        export_to_csv(column2, output_path + "c2.csv")




output_file = "final.csv"
pdf_path = [
    "C:/Users/Hurel Roques Tom/Desktop/Stage Lexika/IAAI/035.pdf",
    "C:/Users/Hurel Roques Tom/Desktop/Stage Lexika/IAAI/036.pdf",
    "C:/Users/Hurel Roques Tom/Desktop/Stage Lexika/IAAI/037.pdf",
    "C:/Users/Hurel Roques Tom/Desktop/Stage Lexika/IAAI/038.pdf"
    ]

output_path = [
    "p35",
    "p36",
    "p37",
    "p38"
    ]


p1c1 = r"C:\Users\Hurel Roques Tom\Desktop\Stage Lexika\iaai csv\p37c1.csv"
p1c2 = r"C:\Users\Hurel Roques Tom\Desktop\Stage Lexika\iaai csv\p37c2.csv"


csv_fusion(p1c1, output_file)
csv_fusion(p1c2, output_file)

# column1 = array_from_txt(column1)
# column2 = array_from_txt(column2)

# export_to_csv(column1, p27c1)
# export_to_csv(column2, p27c2)






# with open(output_file, "w", encoding="utf-8") as f:
#     f.write("Textes de la colonne 1:\n")
#     for box in array_boxes:
#         if box["column"] == 1:
#             bold_info = "Oui" if box["bold"] else "Non"
#             f.write(f"Texte: {box['text']}, Gras: {bold_info}, Pourcent: {box['bold_percent']}\n")

#     f.write("\nTextes de la colonne 2:\n")
#     for box in array_boxes:
#         if box["column"] == 2:
#             bold_info = "Oui" if box["bold"] else "Non"
#             f.write(f"Texte: {box['text']}, Gras: {bold_info}, Pourcent: {box['bold_percent']}\n")

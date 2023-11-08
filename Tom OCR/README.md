# Librairires 

  -pytesseract  
  -fitz  
  -cv2  
  -numpy   
  -pathlib   
  -csv  
  
## Installation

Afin de téléchargé en tant qu'administrateur, pour être sûr que les extensions sont bien installées, on lance les lignes suivantes :

```bash
pip install pymupdf --user
pip install pdfminer --user
pip install pymupdf --user
pip install tqdm --user
pip install numpy --user
pip install pytesseract --user
```

## Lancer l'OCR

Les lignes suivantes permettent de lancer l'ocr et de redirigé les données récupérées dans un fichier csv.

```python
# Chemin du fichier PDF d'entrée
pdf_path = "chemin/vers/votre/fichier.pdf"

# Chemin de sortie pour les fichiers CSV
output_csv_path = "chemin/vers/votre/dossier/de/sortie/"

# Exécutez la fonction get_array_tess pour extraire le texte du PDF.
array_boxes = get_array_tess(pdf_path, test_bold=True, bold_aprox=0.1)

# Traitez le texte et créez deux colonnes.
column1, column2 = order_text(array_boxes)

# Créez des paires de texte à partir de chaque colonne.
column1 = array_from_txt(column1)
column2 = array_from_txt(column2)

# Exportez les données vers des fichiers CSV.
export_to_csv(column1, output_csv_path + "column1.csv")
export_to_csv(column2, output_csv_path + "column2.csv")
```


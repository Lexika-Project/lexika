
# Lexica


# Lancer l'OCR : (être dans le dossier ocr)
- **Programme nécessaire :**
  - *Clicker [ici](https://www.python.org/downloads/) pour installer Python*
  - *Clicker [ici](https://github.com/UB-Mannheim/tesseract/wiki) pour installer Tesseract*
- **Instalation des packages Pyhton :**
  - *pip install requirements.txt*
- **Initialisation :**
  - *Mettre le dossier Tesseract-OCR dans le dossier `lib`*
  - *Mettre les PDFs avec lesquels vous voulez travailler dans le dossier `pdf`
- **Lancement du programme :**
  - *`python tesseract_miner.py --help` pour plus d'info*
  - *`python tesseract_miner.py --process {num} --filename {nom_du_fichier} --output {type_du_fichier_de_sortie} --page {numero_de_page}`*
- **Ajouter un livre :**
  - *modifier la fonciton `get_parser()` pour ajouter une entrée a l'argument proccess `choices=[*range(2), -1],` => `choices=[*range(3), -1],` (modifier la variable help au passage)*
  - *modifier la fonction `getProcess()` pour lié le nouveau numero a la fonction créer pour gérer le livre ansi que les pages a scanner exemple:*
    ```python     
        case 2:
            process = iaai
            START = 27
            END = 135
    ```
  - *Créer la fonction qui va gérer le livre exemple la fonction hienghene ou nyelayu, la fonction type ressemble a ca :*
    ```python
    def concat_not_bold(elem1, elem2, array):
        if elem1["bold"] or elem2["bold"]:
            return False
        return overlap(elem1, elem2, tolerence_left=100)

    def fonction_type(pdf_img, file_output_name, csv, output_type, debug, num_page=0):
        array_boxe, img, img_height, img_width = get_array_tess(pdf_img, test_bold=True)#si test_bold est True la fonction test si les mots scanner son en gras
        array_boxe = suppr_overlap(array_boxe) #supprime les boites qui se chevauche
        array_boxe = concat_box(
            array_boxe,
            concat_not_bold,
            debug,
            pdf_page=img,
            file_output_name=file_output_name,
            num_page=num_page,
        )
        if output_type == "img":
            save_as_img(array_boxe, img, file_output_name, num_page)
        else:
            draw_pdf(array_boxe, pdf_img, num_page, img_width, img_height)

        res = single_language_array_to_line(array_boxe)
        for elem in res:
            csv.write(elem + ";" + str(num_page) + "\n")
        return
    ```
# Lancer le site en local : (être dans le dossier site)
- **Programme nécessaire :**
  - *Clicker [ici](https://www.python.org/downloads/) pour installer Python*
  - *Clicker [ici](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads) pour installer Postgres*
- **Instalation des packages Pyhton :**
  - *`pip install -r requirements.txt`*
- **Initialisation de la base de données :**
  - *Mettre le dossier `PostgreSQL\15\bin` dans le path pour utiliser la commande psql ([une aide si vous ne savez pas faire](https://www.malekal.com/comment-modifier-la-variable-path-sous-windows-10-11/),par defaut c'est :`C:\\PostgreSQL\15\bin`)*
  - *se connecter a la base de données en tant que postgres (`psql --username=postgres` a éxecuter dans un invite de commande(win + r et taper cmd))*
  - *`create user lexika password 'lexika';`*
  - *`create database lexika with owner lexika;`*
  - *Créer un fichier .env qui contient*
    ```ini
    HOST=localhost
    PORT=5432
    DATABASE=lexika
    USER=lexika
    PASSWORD=lexika
    ```
  - *double clicker sur database.py*
- **Lancer le serveur :**
  - *double clicker sur server.py*
  - *aller a l'url http://localhost*
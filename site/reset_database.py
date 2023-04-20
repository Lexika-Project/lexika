from database import (
    reset_table,
    hienghene_process,
    unique_langue_process,
    add_langue,
    CONN_PARAMS,
)
from tqdm import tqdm
import psycopg


def insert_from_csv(
    cur, filename, liste_langue, add_line_func
):  # pylint: disable=missing-function-docstring
    filename_csv = "release/" + filename + ".csv"

    cur.execute(
        "INSERT INTO livre (nom_livre) VALUES (%(filename)s);",
        {"filename": filename},
    )
    for langue in liste_langue:
        add_langue(cur, langue, filename)
    with open(filename_csv, "r", encoding="utf-8") as file:
        liste_line = file.readlines()
        with tqdm(total=len(liste_line), desc=filename) as pbar:
            global count_sens
            for line in liste_line:
                add_line_func(cur, line, liste_langue, filename, count_sens)
                count_sens += 1
                pbar.update()


count_sens = 0

if __name__ == "__main__":
    reset_table()
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            insert_from_csv(
                cur,
                "hienghene-Fr",
                [
                    "français",
                    "pije",
                    "fwâi",
                    "nemi 1 (Temala)",
                    "nemi 2 (côte est)",
                    "jawe",
                ],
                hienghene_process,
            )
            insert_from_csv(
                cur,
                "le_nyelayu_de_balade",
                [
                    "nyelayu",
                    "français",
                ],
                unique_langue_process,
            )

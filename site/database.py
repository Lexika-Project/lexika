"""_summary_

Returns:
    _type_: _description_
"""
import os
import urllib.parse
import psycopg

from dotenv import dotenv_values

os.chdir(os.path.dirname(__file__))

if os.path.exists(".env"):
    config = dotenv_values(".env")
else:
    config = dotenv_values("default.env")


FILENAME_DB_SHEMA = "database/database.sql"
FILENAME_FUNCTION_SHEMA = "database/function.sql"
options = urllib.parse.quote_plus("--search_path=modern,public")
CONN_PARAMS = f"postgresql://{config['USER']}:{config['PASSWORD']}@{config['HOST']}:{config['PORT']}/{config['DATABASE']}?options={options}"  # pylint: disable=line-too-long


def update_function():  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            with open(FILENAME_FUNCTION_SHEMA, "r", encoding="utf-8") as file:
                cur.execute(file.read())
                print("function update !")


def reset_table():  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            with open(FILENAME_DB_SHEMA, "r", encoding="utf-8") as file:
                cur.execute(file.read())
            with open(FILENAME_FUNCTION_SHEMA, "r", encoding="utf-8") as file:
                cur.execute(file.read())


def add_langue(cur, langue, livre):  # pylint: disable=missing-function-docstring
    cur.execute(
        """INSERT INTO langue (nom_langue) VALUES (%(langue)s)
        ON CONFLICT (nom_langue) DO NOTHING;""",
        {"langue": langue},
    )
    cur.execute(
        """INSERT INTO langue_dans_un_livre (id_livre,id_langue)
        VALUES (get_id_livre(%(livre)s),get_id_langue(%(langue)s));""",
        {"langue": langue, "livre": livre},
    )


def hienghene_process(
    cur, line, _, livre, count
):  # pylint: disable=missing-function-docstring
    liste_line = line.split(";")
    num_page = liste_line[len(liste_line) - 1]
    del liste_line[len(liste_line) - 1]
    requete = "INSERT INTO data (id_langue , sens , numero_page,id_livre,error) VALUES"
    requete2 = "INSERT INTO version (id_data,traduction) VALUES"
    for element in liste_line:
        element_array = element.split("#@#")
        langue = element_array[0]
        text = element_array[1]
        error = element_array[2]
        if text != "":
            text = text.replace("'", "''")
            int_error = 0
            if error == "True":
                int_error = 1
            requete += f"""
                ((select get_id_langue('{langue}')),'{count}','{num_page}',(select get_id_livre('{livre}')),{int_error}),"""
            requete2 += f"""
                        ((select get_id_data({count},'{langue}')),'{text}'),"""

    requete = requete[0 : len(requete) - 1] + ";"
    requete2 = requete2[0 : len(requete2) - 1] + ";"
    cur.execute(requete)
    cur.execute(requete2)


def unique_langue_process(cur, line, liste_langue, livre, count):
    liste_line = line.split(";")
    num_page = liste_line[len(liste_line) - 1]
    del liste_line[len(liste_line) - 1]
    requete = "INSERT INTO data (id_langue , sens , numero_page,id_livre,error) VALUES"
    requete2 = "INSERT INTO version (id_data,traduction) VALUES"
    for index, element in enumerate(liste_line):
        text = element
        if text != "":
            langue = liste_langue[index]
            text = text.replace("'", "''")
            int_error = 0
            requete += f"""
                ((select get_id_langue('{langue}')),'{count}','{num_page}',(select get_id_livre('{livre}')),{int_error}),"""
            requete2 += f"""
                        ((select get_id_data({count},'{langue}')),'{text}'),"""

    requete = requete[0 : len(requete) - 1] + ";"
    requete2 = requete2[0 : len(requete2) - 1] + ";"
    cur.execute(requete)
    cur.execute(requete2)


def modif_data(langue, text, sens):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO version (id_data,traduction)
                        VALUES((select get_id_data(%(sens)s,%(langue)s)),%(text)s)""",
                {
                    "langue": langue,
                    "text": text,
                    "sens": sens,
                },
            )


def search(
    keyword, engine, langue, langue_base, offset
):  # pylint: disable=missing-function-docstring

    res = []
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            # argument a la place {} ~ a la place de like
            # https://www.postgresql.org/docs/current/functions-matching.html#FUNCTIONS-POSIX-REGEXP
            # enfin https://www.postgresql.org/docs/current/pgtrgm.html
            # peut etre https://www.postgresql.org/docs/current/fuzzystrmatch.html
            # apres https://www.postgresql.org/docs/current/textsearch.html

            # * TSQUERY

            # * METAPHONE
            # cur.execute(
            #     """
            #     SELECT DISTINCT count(sens) FROM dataid_langue=
            #         WHERE dmetaphone(traduction) = dmetaphone(%(keyword)s)
            #         AND id_langue=(select get_id_langue(%(langueBase)s))""",
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #     },
            # )
            # count = cur.fetchone()[0]
            # print(count)
            # cur.execute(
            #     """
            #     SELECT DISTINCT sens FROM data
            #         WHERE dmetaphone(traduction) = dmetaphone(%(keyword)s)
            #         AND id_langue=(select get_id_langue(%(langueBase)s))
            #         ORDER BY sens
            #         LIMIT 25
            #         OFFSET %(offset)s;
            #         """,
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #         "offset": offset,
            #     },
            # )

            # * SIMILARITY
            # cur.execute(
            #     """
            #     SELECT DISTINCT count(sens) FROM data
            #         WHERE similarity(traduction,%(keyword)s) > 0.3
            #         AND id_langue=(select get_id_langue(%(langueBase)s))""",
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #     },
            # )
            # count = cur.fetchone()[0]
            # print(count)
            # cur.execute(
            #     """
            #     SELECT sens,similarity(traduction,%(keyword)s),nom_langue FROM data
            #         WHERE similarity(traduction,%(keyword)s) > 0.3
            #         AND id_langue=(select get_id_langue(%(langueBase)s))
            #         ORDER BY sens
            #         LIMIT 25
            #         OFFSET %(offset)s;
            #         """,
            #     {
            #         "keyword": keyword,
            #         "langueBase": langue_base,
            #         "offset": offset,
            #     },
            # )
            cur.execute(
                "SELECT get_count_by_engine(%(keyword)s,%(engine)s,%(langue_base)s,%(langue_target)s)",
                {
                    "keyword": keyword,
                    "engine": engine,
                    "langue_base": langue_base,
                    "langue_target": langue,
                },
            )
            count = cur.fetchone()[0]
            cur.execute(
                "Select * from search(%(keyword)s,%(engine)s,%(langue)s,%(langue_base)s,%(offset)s)",
                {
                    "keyword": keyword,
                    "engine": engine,
                    "langue": langue,
                    "langue_base": langue_base,
                    "offset": offset,
                },
            )
            res = cur.fetchall()

    return [res, count]


def get_page_db(livre, num_page):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """SELECT * FROM search_by_page(%(num_page)s,%(livre)s)""",
                {"livre": livre, "num_page": num_page},
            )
            return cur.fetchall()


def history(sens, langue):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """SELECT date_creation,traduction FROM complete_table
                    WHERE sens=%(sens)s and nom_langue=%(langue)s
                    ORDER BY date_creation desc;""",
                {"sens": sens, "langue": langue},
            )
            return cur.fetchall()


def list_langue(livre="all"):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            if livre == "all":
                cur.execute("SELECT nom_langue FROM langue;")
            else:
                cur.execute(
                    """SELECT nom_langue FROM langue
                    WHERE id_langue IN (SELECT id_langue
                                    FROM langue_dans_un_livre
                                    WHERE id_livre = (SELECT get_id_livre(%(livre)s)))
                            """,
                    {"livre": livre},
                )
            tempory = cur.fetchall()
            res = []
            for langue in tempory:
                res.append(langue[0])
            return res


def nb_page(livre):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """SELECT nom_langue FROM langue
                WHERE id_langue IN (SELECT id_langue
                                FROM langue_dans_un_livre
                                WHERE id_livre = (SELECT get_id_livre(%(livre)s)))
                        """,
                {"livre": livre},
            )
            tempory = cur.fetchall()
            print(tempory)
            res = []
            for langue in tempory:
                res.append(langue[0])
            return res


def update_link(sens, langue, audio_link):  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE data set audio_link = %(audio_link)s
                    WHERE id_data IN (SELECT id_data FROM data_current
                                        WHERE nom_langue=%(langue)s AND sens=%(sens)s)""",
                {"audio_link": audio_link, "langue": langue, "sens": sens},
            )


def get_error():  # pylint: disable=missing-function-docstring
    with psycopg.connect(CONN_PARAMS) as conn:  # pylint: disable=not-context-manager
        with conn.cursor() as cur:
            cur.execute(
                """
                        SELECT nom_langue FROM langue WHERE id_langue IN (
                            SELECT DISTINCT id_langue FROM data WHERE error = 1);
                        """
            )
            liste_langue = cur.fetchall()
            cur.execute(
                """SELECT date_creation,traduction FROM data_current
                    JOIN langue ON data.id_langue = langue.id_langue
                        WHERE error = 1
                        ORDER BY date_creation desc;"""
            )
            error_table = cur.fetchall()
            return (liste_langue, error_table)





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

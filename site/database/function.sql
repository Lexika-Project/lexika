DROP EXTENSION IF EXISTS pg_trgm;

DROP FUNCTION IF EXISTS get_id_langue;
CREATE OR REPLACE FUNCTION get_id_langue(l langue.nom_langue%TYPE)
    RETURNS SETOF langue.id_langue%TYPE AS
    $$
        SELECT id_langue FROM langue WHERE nom_langue = l
    $$
    LANGUAGE SQL
    STABLE;

DROP FUNCTION IF EXISTS get_id_livre;
CREATE OR REPLACE FUNCTION get_id_livre(l livre.nom_livre%TYPE)
    RETURNS SETOF livre.id_livre%TYPE AS
    $$
        SELECT id_livre FROM livre WHERE nom_livre = l
    $$
    LANGUAGE SQL
    STABLE;
DROP FUNCTION IF EXISTS get_id_data;
CREATE OR REPLACE FUNCTION get_id_data(sens_to_find data.sens%TYPE,langue_to_find livre.nom_livre%TYPE)
    RETURNS SETOF data.id_data%TYPE AS
    $$
        SELECT id_data FROM data WHERE sens=sens_to_find AND id_langue=(SELECT get_id_langue(langue_to_find))
    $$
    LANGUAGE SQL
    STABLE;
DROP FUNCTION IF EXISTS tsquery_engine;
CREATE OR REPLACE FUNCTION tsquery_engine(keyword version.traduction%TYPE, langue_base langue.nom_langue%TYPE)
    RETURNS TABLE(
        sens int
    )
    LANGUAGE plpgsql AS
    $tsquery_engine$
    BEGIN
        RETURN QUERY
            SELECT data_current.sens FROM data_current 
            WHERE to_tsvector(data_current.traduction) @@ to_tsquery(keyword)
            AND data_current.nom_langue = langue_base;
    END
    $tsquery_engine$;

DROP FUNCTION IF EXISTS regex_engine;
CREATE OR REPLACE FUNCTION regex_engine(keyword version.traduction%TYPE, langue_base langue.nom_langue%TYPE)
    RETURNS TABLE(
        sens int
    )
    LANGUAGE plpgsql AS
    $regex_engine$
    BEGIN
        RETURN QUERY
        SELECT data_current.sens FROM data_current 
                WHERE data_current.traduction ~* keyword
                AND data_current.nom_langue = langue_base;
    END
    $regex_engine$;
DROP FUNCTION IF EXISTS get_result;
CREATE OR REPLACE FUNCTION get_result(keyword version.traduction%TYPE, engine text, langue_base langue.nom_langue%TYPE)
    RETURNS TABLE(
        sens int
    )
    LANGUAGE plpgsql AS
    $get_result$
    BEGIN
            IF engine = 'regex' THEN
                RETURN QUERY
                SELECT * FROM regex_engine(keyword,langue_base);
            ELSIF engine = 'tsquery' THEN
                RETURN QUERY
                SELECT * FROM tsquery_engine(keyword,langue_base);
            END IF;
    END
    $get_result$;



DROP FUNCTION IF EXISTS search;
CREATE OR REPLACE FUNCTION search(keyword version.traduction%TYPE,engine text, langue_target langue.nom_langue%TYPE, langue_base langue.nom_langue%TYPE, offset_num int)
    RETURNS TABLE(
        nom_langue langue.nom_langue%TYPE,
        traduction version.traduction%TYPE,
        sens data.sens%TYPE,
        numeroPage int,
        nom_livre text,
        audio_link text
    )
    LANGUAGE plpgsql AS
    $funcSearch$
    BEGIN
        RETURN QUERY
        SELECT data_current.nom_langue,data_current.traduction,data_current.sens,data_current.numero_page , data_current.nom_livre , data_current.audio_link
            FROM data_current
            WHERE  data_current.sens in (SELECT data_current.sens 
                                    FROM data_current 
                                    where data_current.sens in (select tmp.sens FROM get_result(keyword,engine,langue_base) as tmp)
                                    AND (langue_target = 'all' or data_current.nom_langue = langue_target)
                                    LIMIT 25
                                    OFFSET offset_num)
            ORDER by data_current.sens;
            
    END
    $funcSearch$;


DROP FUNCTION IF EXISTS search_by_page;
CREATE OR REPLACE FUNCTION search_by_page(page int, livre livre.nom_livre%TYPE)
    RETURNS TABLE(
        nom_langue text,
        traduction text,
        sens int
    )
    LANGUAGE plpgsql AS
    $funcSearch$
    BEGIN
        RETURN QUERY
        SELECT data_current.nom_langue,data_current.traduction,data_current.sens
                        FROM data_current
                        WHERE data_current.numero_page = page AND data_current.nom_livre = livre ORDER BY data_current.sens;   
    END
    $funcSearch$;

DROP FUNCTION IF EXISTS get_count_by_engine;
CREATE OR REPLACE FUNCTION get_count_by_engine(keyword text,engine text , langue_base langue.nom_langue%TYPE , langue_target langue.nom_langue%TYPE)
    RETURNS int
    LANGUAGE plpgsql  AS
    $$
    BEGIN
        RETURN (SELECT count(*)
            From
            (select DISTINCT data_current.sens
            FROM data_current
            WHERE  data_current.sens in (SELECT data_current.sens 
                                    FROM data_current 
                                    where data_current.sens in (select tmp.sens FROM get_result(keyword,engine,langue_base) as tmp)
                                    AND (langue_target = 'all' or  data_current.nom_langue = langue_target))
            ORDER by data_current.sens) as tmp2);
    END
    $$;
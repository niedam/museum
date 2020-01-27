CREATE VIEW no_exhibits AS SELECT * FROM artists WHERE id NOT IN (SELECT artist FROM exhibits WHERE artist IS NOT NULL);

CREATE VIEW no_exhibited AS SELECT artists.id, artists.name, artists.surname FROM artists LEFT JOIN
(SELECT eh.*, exhibits.artist FROM exhibits LEFT JOIN
    (SELECT * FROM exhibits_history WHERE exhibited_in IS NOT NULL AND current_date BETWEEN since_date AND to_date) eh
ON eh.exhibit = exhibits.id) eh2 ON eh2.artist = artists.id group by artists.id, artists.name, artists.surname having count(eh2.id) = 0;

CREATE FUNCTION storage_query (since DATE, tod DATE) RETURNS
    TABLE(id INTEGER, title VARCHAR(255), id_a INTEGER, name VARCHAR(255), surname VARCHAR(255), type VARCHAR(255)) AS $$
BEGIN
    IF since IS NULL AND tod IS NULL THEN
        since = current_date;
        tod = current_date;
    END IF;
    IF since IS NULL THEN
        since := (SELECT min(since_date) FROM exhibits_history);
    END IF;
    IF tod IS NULL THEN
        tod := (SELECT max(to_date) FROM exhibits_history);
    END IF;
    RETURN QUERY SELECT e.id, e.title, a.id, a.name, a.surname, e.type FROM exhibits e LEFT JOIN artists a on e.artist = a.id
    WHERE e.id NOT IN (SELECT eh2.exhibit FROM exhibits_history eh2
                       WHERE (eh2.since_date BETWEEN since AND tod) OR (eh2.to_date BETWEEN since AND tod)
                       OR (since BETWEEN eh2.since_date AND eh2.to_date) OR (tod BETWEEN eh2.since_date AND eh2.to_date));
END;
$$ LANGUAGE plpgsql;

CREATE FUNCTION collision () RETURNS TRIGGER AS $$
BEGIN
        IF (SELECT count(*) FROM exhibits_history e
            WHERE NEW.exhibit = e.exhibit AND (NEW.since_date BETWEEN e.since_date AND e.to_date
                                                   OR NEW.to_date BETWEEN e.since_date AND e.to_date )) != 0 THEN
            RAISE EXCEPTION 'collision';
        END IF;
        RETURN NEW;
    END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER collision_trigger BEFORE INSERT OR UPDATE ON exhibits_history FOR EACH ROW EXECUTE PROCEDURE collision ();
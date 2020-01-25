CREATE VIEW no_exhibition AS SELECT a.id, a.name, a.surname FROM artists a LEFT JOIN exhibits e on a.id = e.artist WHERE e.id IS NULL;


CREATE VIEW no_exhibited AS SELECT artists.id, artists.name, artists.surname FROM artists LEFT JOIN
(SELECT eh.*, exhibits.artist FROM exhibits LEFT JOIN
    (SELECT * FROM exhibits_history WHERE exhibited_in IS NOT NULL AND current_date BETWEEN since_date AND to_date) eh
ON eh.exhibit = exhibits.id) eh2 ON eh2.artist = artists.id group by artists.id, artists.name, artists.surname having count(eh2.id) = 0;

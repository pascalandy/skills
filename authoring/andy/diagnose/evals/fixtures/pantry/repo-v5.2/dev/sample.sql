-- Sample data for local runs and tests: 300 recipes, their tags, 4,000 reviews.
-- Same schema as the production database. Rows are generated so the file stays small.

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    total_minutes INTEGER NOT NULL,
    serves INTEGER NOT NULL,
    author TEXT NOT NULL,
    saves INTEGER NOT NULL DEFAULT 0,
    published INTEGER NOT NULL DEFAULT 1,
    updated_at TEXT NOT NULL
);

CREATE TABLE recipe_tags (
    recipe_id INTEGER NOT NULL REFERENCES recipes (id),
    tag TEXT NOT NULL,
    PRIMARY KEY (recipe_id, tag)
);
CREATE INDEX recipe_tags_by_tag ON recipe_tags (tag, recipe_id);

CREATE TABLE reviews (
    id INTEGER PRIMARY KEY,
    recipe_id INTEGER NOT NULL REFERENCES recipes (id),
    stars INTEGER NOT NULL CHECK (stars BETWEEN 1 AND 5),
    created_at TEXT NOT NULL
);
CREATE INDEX reviews_by_recipe ON reviews (recipe_id);

CREATE TEMP TABLE mains (n INTEGER PRIMARY KEY, name TEXT, tag TEXT, vegetarian INTEGER);
INSERT INTO mains VALUES
    (0, 'Chicken', 'chicken', 0),
    (1, 'Salmon', 'salmon', 0),
    (2, 'Tofu', 'tofu', 1),
    (3, 'Chickpea', 'chickpea', 1),
    (4, 'Beef', 'beef', 0),
    (5, 'Pork', 'pork', 0),
    (6, 'Shrimp', 'shrimp', 0),
    (7, 'Mushroom', 'mushroom', 1),
    (8, 'Lentil', 'lentil', 1),
    (9, 'Halloumi', 'halloumi', 1);

CREATE TEMP TABLE dishes (n INTEGER PRIMARY KEY, name TEXT, tag TEXT, minutes INTEGER);
INSERT INTO dishes VALUES
    (0, 'Tacos', 'tacos', 25),
    (1, 'Curry', 'curry', 40),
    (2, 'Traybake', 'traybake', 45),
    (3, 'Noodle Bowl', 'noodles', 20),
    (4, 'Soup', 'soup', 35),
    (5, 'Salad', 'salad', 15),
    (6, 'Skewers', 'grill', 30),
    (7, 'Pasta', 'pasta', 25),
    (8, 'Stew', 'stew', 85),
    (9, 'Fried Rice', 'rice', 20);

CREATE TEMP TABLE styles (n INTEGER PRIMARY KEY, name TEXT, tag TEXT, extra INTEGER);
INSERT INTO styles VALUES
    (0, 'Smoky', 'smoky', 10),
    (1, 'Lemon Herb', 'bright', 0),
    (2, 'Sticky Sesame', 'sesame', 5),
    (3, 'Coconut', 'coconut', 5),
    (4, 'Harissa', 'spicy', 5),
    (5, 'Garlic Butter', 'rich', 0),
    (6, 'Green Chile', 'spicy', 10),
    (7, 'Miso', 'miso', 5);

CREATE TEMP TABLE authors (n INTEGER PRIMARY KEY, name TEXT);
INSERT INTO authors VALUES
    (0, 'Odile Ferrand'),
    (1, 'Kwabena Lowe'),
    (2, 'Rosa Ibarguen'),
    (3, 'Henrik Saelid'),
    (4, 'Mei-Lin Okoro'),
    (5, 'Tobias Wren');

CREATE TEMP TABLE notes (n INTEGER PRIMARY KEY, text TEXT);
INSERT INTO notes VALUES
    (0, 'Good on a weeknight, and the leftovers keep for two days.'),
    (1, 'Most of the cooking is hands-off once everything is in the pan.'),
    (2, 'Make the sauce a day ahead and it comes together in minutes.'),
    (3, 'Doubles well; freeze half for later.');

-- Three recipes per main and dish, each in a different style.
CREATE TEMP TABLE plan AS
SELECT m.n * 30 + d.n * 3 + k.n + 1 AS id, m.n AS m, d.n AS d, s.n AS s
FROM mains m, dishes d,
     (SELECT 0 AS n UNION ALL SELECT 1 UNION ALL SELECT 2) k,
     styles s
WHERE s.n = (m.n * 3 + d.n + k.n * 3) % 8;

INSERT INTO recipes (id, slug, title, summary, total_minutes, serves, author, saves, published, updated_at)
SELECT p.id,
       lower(replace(s.name || ' ' || m.name || ' ' || d.name, ' ', '-')) || '-' || p.id,
       s.name || ' ' || m.name || ' ' || d.name,
       'Serves ' || (2 + (p.id % 3) * 2) || ', ready in '
           || (d.minutes + s.extra + (p.id % 3) * 5) || ' minutes. ' || nt.text,
       d.minutes + s.extra + (p.id % 3) * 5,
       2 + (p.id % 3) * 2,
       a.name,
       (p.id * 7919) % 4800 + 40,
       CASE WHEN p.id % 97 = 0 THEN 0 ELSE 1 END,
       datetime('2024-01-08 09:00:00', '+' || ((p.id * 7703) % 990) || ' days',
                '+' || ((p.id * 37) % 600) || ' minutes')
FROM plan p
JOIN mains m ON m.n = p.m
JOIN dishes d ON d.n = p.d
JOIN styles s ON s.n = p.s
JOIN authors a ON a.n = (p.id * 7) % 6
JOIN notes nt ON nt.n = p.id % 4;

INSERT INTO recipe_tags SELECT p.id, m.tag FROM plan p JOIN mains m ON m.n = p.m;
INSERT INTO recipe_tags SELECT p.id, d.tag FROM plan p JOIN dishes d ON d.n = p.d;
INSERT INTO recipe_tags SELECT p.id, s.tag FROM plan p JOIN styles s ON s.n = p.s;
INSERT INTO recipe_tags SELECT p.id, 'vegetarian' FROM plan p JOIN mains m ON m.n = p.m WHERE m.vegetarian = 1;
INSERT INTO recipe_tags SELECT id, 'quick' FROM recipes WHERE total_minutes <= 30;
INSERT INTO recipe_tags SELECT id, 'weeknight' FROM recipes WHERE total_minutes <= 45;

INSERT INTO reviews (id, recipe_id, stars, created_at)
WITH RECURSIVE seq (i) AS (SELECT 1 UNION ALL SELECT i + 1 FROM seq WHERE i < 4000)
SELECT i,
       1 + (i * 7919 + (i * i) / 37) % 300,
       CASE (i * 37 + i / 7) % 20
           WHEN 0 THEN 1
           WHEN 1 THEN 2
           WHEN 2 THEN 3
           WHEN 3 THEN 3
           WHEN 4 THEN 4 WHEN 5 THEN 4 WHEN 6 THEN 4 WHEN 7 THEN 4 WHEN 8 THEN 4 WHEN 9 THEN 4
           ELSE 5
       END,
       date('2025-01-02', '+' || ((i * 131) % 640) || ' days')
FROM seq;

DROP TABLE plan;
DROP TABLE notes;
DROP TABLE authors;
DROP TABLE styles;
DROP TABLE dishes;
DROP TABLE mains;

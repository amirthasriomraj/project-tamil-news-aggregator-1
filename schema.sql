CREATE TABLE websites (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE news_details (
    id SERIAL PRIMARY KEY,
    website_id INT REFERENCES websites(id),
    website_name VARCHAR(50),
    title TEXT NOT NULL,
    article_url TEXT UNIQUE NOT NULL,
    image_url TEXT,
    category TEXT,
    published_time TEXT,
    language TEXT DEFAULT 'Tamil',
    author TEXT,
    description TEXT
);


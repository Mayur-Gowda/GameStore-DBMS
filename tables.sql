CREATE TABLE games (
  game_id INT PRIMARY KEY AUTO_INCREMENT,
  game_name VARCHAR(255),
  details TEXT,
  developer VARCHAR(255),
  publisher VARCHAR(255),
  platform VARCHAR(255),
  price DECIMAL(4,2)
);

CREATE TABLE users (
  user_id INT PRIMARY KEY AUTO_INCREMENT,
  username VARCHAR(255) UNIQUE,
  phone VARCHAR(15),
  address VARCHAR(255),
  email VARCHAR(255) UNIQUE,
  password_hash TEXT
);

CREATE TABLE user_orders (
  order_id INT PRIMARY KEY AUTO_INCREMENT,
  date_order DATE,
  user_id INT,
  FOREIGN KEY (user_id)
    REFERENCES users (user_id)
    ON DELETE CASCADE ON UPDATE CASCADE
) AUTO_INCREMENT = 140101;

CREATE TABLE order_items (
  order_id INT,
  game_id INT,
  FOREIGN KEY (order_id)
    REFERENCES user_orders (order_id)
    ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (game_id)
    REFERENCES games (game_id)
    ON DELETE CASCADE ON UPDATE CASCADE
);

CREATE TABLE game_inventory (
  game_id INT PRIMARY KEY,
  games_count INT,
  FOREIGN KEY (game_id)
    REFERENCES games (game_id)
    ON DELETE CASCADE ON UPDATE CASCADE
);


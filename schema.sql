CREATE DATABASE IF NOT EXISTS student_dashboard;
use student_dashboard;	
CREATE TABLE user_data(
	id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(30) NOT NULL,
    password VARCHAR(100) NOT NULL
    );
CREATE TABLE subjects(
	sub_id INT AUTO_INCREMENT PRIMARY KEY,
    sub_name VARCHAR(50) NOT NULL,
    max_marks INT NOT NULL
    );
CREATE TABLE results(
	res_id INT AUTO_INCREMENT PRIMARY KEY,
    st_id INT,
    sb_id INT,
    FOREIGN KEY (st_id) REFERENCES user_data(id),
    FOREIGN KEY (sb_id) REFERENCES subjects(sub_id)
    );
USE student_dashboard;
ALTER TABLE results
ADD COLUMN marks INT;
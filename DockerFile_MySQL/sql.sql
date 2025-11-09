use profesor_virtual_mysql;

CREATE TABLE profesor(
    id_profesor INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    apellidos VARCHAR(50),
    edad INT,
    email VARCHAR(50),
    telefono VARCHAR(20)
);

CREATE TABLE alumno(
    id_alumno INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    apellidos VARCHAR(50),
    edad INT,
    email VARCHAR(50),
    telefono VARCHAR(20)
);

CREATE TABLE asignatura(
    id_asignatura INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50),
    id_profesor INT,
    curso VARCHAR(10),
    FOREIGN KEY (id_profesor) REFERENCES profesor(id_profesor)
);
CREATE TABLE alumno_asignatura (
    id_alumno INT,
    id_asignatura INT,
    PRIMARY KEY (id_alumno, id_asignatura),
    FOREIGN KEY (id_alumno) REFERENCES alumno(id_alumno),
    FOREIGN KEY (id_asignatura) REFERENCES asignatura(id_asignatura)
);

CREATE TABLE informe(
    id_informe INT PRIMARY KEY AUTO_INCREMENT,
    id_profesor INT,
    id_alumno INT,
    descripcion TEXT,
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
);




CREATE TABLE conducta(
    id_conducta int PRIMARY KEY AUTO_INCREMENT,
    id_alumno int,
    id_profesor int,
    id_asignatura int,
    descripcion TEXT,
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
);

CREATE Table calificacion_examen(
    id_calificacion INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_profesor INT,
    id_alumno INT,
    calificacion DOUBLE,
    unidad VARCHAR(50),
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
);

CREATE Table calificacion_practica(
    id_calificacion INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_profesor INT,
    id_alumno INT,
    calificacion DOUBLE,
    unidad VARCHAR(50),
    fecha DATE,
    Foreign Key (id_profesor) REFERENCES profesor(id_profesor),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
);

CREATE TABLE interes(
    id_interes INT PRIMARY KEY AUTO_INCREMENT,
    id_alumno INT,
    resumen VARCHAR(255),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
);

CREATE TABLE alumno_interes (
    id_alumno INT,
    id_interes INT,
    PRIMARY KEY (id_alumno, id_interes),
    FOREIGN KEY (id_alumno) REFERENCES alumno(id_alumno),
    FOREIGN KEY (id_interes) REFERENCES interes(id_interes)
);

CREATE TABLE ejercicio(
    id_ejercicio INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_interes int,
    id_alumno INT,
    contenido TEXT,
    dificultad VARCHAR(10),
    unidad VARCHAR(50),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno),
    Foreign Key (id_asignatura) REFERENCES asignatura(id_asignatura),
    Foreign Key (id_interes) REFERENCES interes(id_interes)
);

CREATE TABLE ejercicio_interes (
    id_ejercicio INT,
    id_interes INT,
    PRIMARY KEY (id_ejercicio, id_interes),
    FOREIGN KEY (id_ejercicio) REFERENCES ejercicio(id_ejercicio),
    FOREIGN KEY (id_interes) REFERENCES interes(id_interes)
);



CREATE Table progreso(
    id_progreso INT PRIMARY KEY AUTO_INCREMENT,
    id_asignatura INT,
    id_alumno INT,
    unidad VARCHAR(50),
    evolucion VARCHAR(255),
    nota_media DOUBLE,
    fecha DATE,
    Foreign Key (id_asignatura) REFERENCES asignatura(id_asignatura),
    Foreign Key (id_alumno) REFERENCES alumno(id_alumno)
);


CREATE TABLE log(
    id_log INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL,
    tipo_usuario ENUM('alumno','profesor') NOT NULL,
    duracion_sesion INT NOT NULL,
    fecha_conexion DATETIME NOT NULL
);

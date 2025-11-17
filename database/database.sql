create database db_trabalho3b;


CREATE TABLE Autores (
    ID_autor INT AUTO_INCREMENT PRIMARY KEY,
    Nome_autor VARCHAR(255) NOT NULL,
    Nacionalidade VARCHAR(255),
    Data_nascimento DATE,
    Biografia TEXT
);

CREATE TABLE Generos (
    ID_genero INT AUTO_INCREMENT PRIMARY KEY,
    Nome_genero VARCHAR(255) NOT NULL
);

CREATE TABLE Editoras (
    ID_editora INT AUTO_INCREMENT PRIMARY KEY,
    Nome_editora VARCHAR(255) NOT NULL,
    Endereco_editora TEXT
);

CREATE TABLE Livros (
    ID_livro INT AUTO_INCREMENT PRIMARY KEY,
    Titulo VARCHAR(255) NOT NULL,
    Autor_id INT,
    ISBN VARCHAR(13) NOT NULL,
    Ano_publicacao INT,
    Genero_id INT,
    Editora_id INT,
    Quantidade_disponivel INT,
    Resumo TEXT,
    FOREIGN KEY (Autor_id) REFERENCES Autores(ID_autor),
    FOREIGN KEY (Genero_id) REFERENCES Generos(ID_genero),
    FOREIGN KEY (Editora_id) REFERENCES Editoras(ID_editora)
);

CREATE TABLE Usuarios (
    ID_usuario INT AUTO_INCREMENT PRIMARY KEY,
    Nome_usuario VARCHAR(255) NOT NULL,
    Email VARCHAR(255),
    Numero_telefone VARCHAR(15),
    Data_inscricao DATE,
    Multa_atual DECIMAL(10, 2)
);

CREATE TABLE Emprestimos (
    ID_emprestimo INT AUTO_INCREMENT PRIMARY KEY,
    Usuario_id INT,
    Livro_id INT,
    Data_emprestimo DATE,
    Data_devolucao_prevista DATE,
    Data_devolucao_real DATE,
    Status_emprestimo ENUM('pendente', 'devolvido', 'atrasado'),
    Livro_genero_id INT NULL,
    Livro_autor_id INT NULL,
    FOREIGN KEY (Usuario_id) REFERENCES Usuarios(ID_usuario),
    FOREIGN KEY (Livro_id) REFERENCES Livros(ID_livro),
    FOREIGN KEY (Livro_genero_id) REFERENCES Generos(ID_genero) ON DELETE RESTRICT,
    FOREIGN KEY (Livro_autor_id) REFERENCES Autores(ID_autor) ON DELETE RESTRICT
);

alter table Usuarios add column Senha varchar(300);
alter table Autores add COLUMN Usuario_id int null;

alter table Livros add COLUMN Usuario_id int null;
alter table Livros 
    add constraint fk_livros_usuarios
    foreign key (Usuario_id) references Usuarios(ID_usuario);

ALTER TABLE Editoras ADD COLUMN Usuario_id INT NULL;
ALTER TABLE Editoras
    ADD CONSTRAINT fk_editoras_usuarios
    FOREIGN KEY (Usuario_id) REFERENCES Usuarios(ID_usuario) ON DELETE SET NULL;
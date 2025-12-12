create database db_trabalho3b;

use db_trabalho3b;
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
    FOREIGN KEY (Usuario_id) REFERENCES Usuarios(ID_usuario),
    FOREIGN KEY (Livro_id) REFERENCES Livros(ID_livro)
);

alter table Usuarios add column Senha varchar(300);

delimiter //

create trigger trg_usuarios_nome_minimo
before insert on usuarios
for each row
begin
    if char_length(new.nome_usuario) < 3 then
        signal sqlstate '45000'
            set message_text = 'o nome do usuário deve ter pelo menos 3 caracteres.';
    end if;
end //

delimiter ;

insert into usuarios values(default, 'jp', 'jp@gmail.com', '(84) 99817-4551', '2007/12/12', 1.54, '123');

delimiter //

create trigger trg_usuarios_nome_minimo_update
before update on usuarios
for each row
begin
    if char_length(new.nome_usuario) < 3 then
        signal sqlstate '45000'
            set message_text = 'o nome do usuário deve ter pelo menos 3 caracteres.';
    end if;
end //

delimiter ;

delimiter //

create trigger trg_livros_isbn_valido
before insert on livros
for each row
begin
    if char_length(new.isbn) <> 13 then
        signal sqlstate '45000'
            set message_text = 'o isbn deve possuir exatamente 13 dígitos.';
    end if;
end //

delimiter ;

delimiter //

create trigger trg_emprestimos_datas_validas
before insert on emprestimos
for each row
begin
    if new.data_devolucao_prevista < new.data_emprestimo then
        signal sqlstate '45000'
            set message_text = 'a data de devolução prevista não pode ser anterior à data de empréstimo.';
    end if;
end //

delimiter ;

delimiter //

create trigger trg_livros_quantidade_valida
before update on livros
for each row
begin
    if new.quantidade_disponivel < 0 then
        signal sqlstate '45000'
            set message_text = 'a quantidade disponível não pode ser negativa.';
    end if;
end //

delimiter ;





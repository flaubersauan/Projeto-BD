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

create table Auditoria_Log (
    id_log int auto_increment primary key,
    tabela_afetada varchar(50),
    operacao enum('INSERT', 'UPDATE', 'DELETE'),
    id_registro_afetado int,
    valor_antigo text,
    valor_novo text,
    data_hora timestamp default current_timestamp
);


alter table Usuarios add column Senha varchar(300);

ALTER TABLE Autores
ADD COLUMN Usuario_id INT,
ADD CONSTRAINT fk_autores_usuarios
FOREIGN KEY (Usuario_id) REFERENCES Usuarios(ID_usuario);

ALTER TABLE Editoras
ADD COLUMN Usuario_id INT,
ADD CONSTRAINT fk_editoras_usuarios
FOREIGN KEY (Usuario_id) REFERENCES Usuarios(ID_usuario);

ALTER TABLE Livros
ADD COLUMN Usuario_id INT,
ADD CONSTRAINT fk_livros_usuarios
FOREIGN KEY (Usuario_id) REFERENCES Usuarios(ID_usuario);




-- Triggers de validação : Flauber Sauan
delimiter //
create trigger trg_usuarios_nome_minimo_update
before update on Usuarios
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
before insert on Livros
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
before insert on Emprestimos
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
before update on Livros
for each row
begin
    if new.quantidade_disponivel < 0 then
        signal sqlstate '45000'
            set message_text = 'a quantidade disponível não pode ser negativa.';
    end if;
end //

delimiter ;


-- 4. Gatilhos de Atualização Automática Pós-Evento : Guilherme

delimiter //

CREATE TRIGGER trg_emprestimo_reduz_quantidade
AFTER INSERT ON Emprestimos
FOR EACH ROW
BEGIN
    UPDATE Livros
    SET Quantidade_disponivel = Quantidade_disponivel - 1
    WHERE ID_livro = NEW.Livro_id;
END //

delimiter ;
-- 4.2 Quando um empréstimo é excluído, devolve automaticamente o livro ao estoque.
delimiter //

CREATE TRIGGER trg_emprestimo_delete_devolve_livro
AFTER DELETE ON Emprestimos
FOR EACH ROW
BEGIN
    UPDATE Livros
    SET Quantidade_disponivel = Quantidade_disponivel + 1
    WHERE ID_livro = OLD.Livro_id;
END //

delimiter ;
-- 4.3 Quando o status muda para “devolvido”, o livro volta automaticamente para o estoque.
delimiter //

CREATE TRIGGER trg_emprestimo_devolvido
AFTER UPDATE ON Emprestimos
FOR EACH ROW
BEGIN
    IF OLD.Status_emprestimo <> 'devolvido'
       AND NEW.Status_emprestimo = 'devolvido' THEN

        UPDATE Livros
        SET Quantidade_disponivel = Quantidade_disponivel + 1
        WHERE ID_livro = NEW.Livro_id;
    END IF;
END //

delimiter ;
-- 4.4 Se o empréstimo estiver atrasado, aplica automaticamente uma multa ao usuário.
DELIMITER //

CREATE TRIGGER trg_emprestimo_multa_atraso
AFTER UPDATE ON Emprestimos
FOR EACH ROW
BEGIN
    IF NEW.Status_emprestimo = 'atrasado'
       AND OLD.Status_emprestimo <> 'atrasado' THEN

        UPDATE Usuarios
        SET Multa_atual = IFNULL(Multa_atual, 0) + 10.00
        WHERE ID_usuario = NEW.Usuario_id;
    END IF;
END //

DELIMITER ;
-- 4.5 Quando um usuário é removido, remove automaticamente a multa associada (limpeza lógica).
delimiter //

CREATE TRIGGER trg_usuario_delete_limpa_multas
AFTER DELETE ON Usuarios
FOR EACH ROW
BEGIN
    UPDATE Usuarios
    SET Multa_atual = 0
    WHERE ID_usuario = OLD.ID_usuario;
END //

delimiter ;

-- Gatilhos de auditoria : Alan Pereira e João Paulo

delimiter //
create trigger tr_auditoria_usuario_insert
after insert on Usuarios
for each row
begin
    insert into Auditoria_Log (tabela_afetada, operacao, id_registro_afetado, valor_novo)
    values ('usuarios', 'insert', new.id_usuario, 
            concat('nome: ', new.nome_usuario, ' | email: ', new.email));
end //
delimiter ;

delimiter //
create trigger tr_auditoria_usuario_update
after update on Usuarios
for each row
begin
    insert into Auditoria_Log (tabela_afetada, operacao, id_registro_afetado, valor_antigo, valor_novo)
    values ('usuarios', 'update', old.id_usuario, 
            concat('multa anterior: ', old.multa_atual), 
            concat('multa nova: ', new.multa_atual));
end //
delimiter ;

delimiter //
create trigger tr_auditoria_livros_delete
after delete on Livros
for each row
begin
    insert into Auditoria_Log (tabela_afetada, operacao, id_registro_afetado, valor_antigo)
    values ('livros', 'delete', old.id_livro, 
            concat('titulo: ', old.titulo, ' | isbn: ', old.isbn));
end //
delimiter ;

select * from Auditoria_Log;

delimiter //
create trigger tr_auditoria_autores_insert
after insert on Autores
for each row
begin
    insert into Auditoria_Log (tabela_afetada, operacao, id_registro_afetado, valor_novo)
    values ('autores', 'insert', new.id_autor, concat('nome: ', new.nome_autor));
end //

delimiter ; 


delimiter //
create trigger tr_auditoria_autores_delete
after delete on Autores
for each row
begin
    insert into auditoria_log (tabela_afetada, operacao, id_registro_afetado, valor_antigo)
    values ('autores', 'delete', old.id_autor, concat('nome: ', old.nome_autor));
end //

delimiter ;


-- Gatilhos de geração de valores : Kaik Emanoel

DELIMITER //

CREATE TRIGGER trg_usuarios_data_inscricao_auto
BEFORE INSERT ON Usuarios
FOR EACH ROW
BEGIN
    IF NEW.Data_inscricao IS NULL THEN
        SET NEW.Data_inscricao = CURDATE();
    END IF;
END//

DELIMITER ;



DELIMITER //

CREATE TRIGGER trg_emprestimos_data_emprestimo_auto
BEFORE INSERT ON Emprestimos
FOR EACH ROW
BEGIN
    IF NEW.Data_emprestimo IS NULL THEN
        SET NEW.Data_emprestimo = CURDATE();
    END IF;
END//

DELIMITER ;


DELIMITER //

CREATE TRIGGER trg_emprestimos_data_devolucao_real_auto
BEFORE UPDATE ON Emprestimos
FOR EACH ROW
BEGIN
    IF NEW.Status_emprestimo = 'devolvido'
       AND OLD.Status_emprestimo <> 'devolvido' THEN
        SET NEW.Data_devolucao_real = CURDATE();
    END IF;
END//

DELIMITER ;


DELIMITER //

CREATE TRIGGER trg_livros_resumo_auto
BEFORE INSERT ON Livros
FOR EACH ROW
BEGIN
    IF NEW.Resumo IS NULL OR NEW.Resumo = '' THEN
        SET NEW.Resumo = 'Resumo gerado automaticamente pelo sistema.';
    END IF;
END//

DELIMITER ;


DELIMITER //

CREATE TRIGGER trg_emprestimos_status_auto
BEFORE INSERT ON Emprestimos
FOR EACH ROW
BEGIN
    IF NEW.Status_emprestimo IS NULL THEN
        SET NEW.Status_emprestimo = 'pendente';
    END IF;
END//

DELIMITER ;

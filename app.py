from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from database import Session

app = Flask(__name__)
app.secret_key = "segredo_muito_seguro"

# Configuração do Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Classe compatível com Flask-Login
class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email


@login_manager.user_loader
def load_user(user_id):
    db = Session()
    try:
        query = text("SELECT ID_usuario, Nome_usuario, Email FROM Usuarios WHERE ID_usuario = :id")
        result = db.execute(query, {"id": user_id}).fetchone()
        
        if result:
            return User(id=result.ID_usuario, nome=result.Nome_usuario, email=result.Email)
        return None
    finally:
        db.close()



@app.route('/')
def index():
    return render_template('index.html')



@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        db = Session()
        try:
            verificar = db.execute(
                text("SELECT * FROM Usuarios WHERE Email = :email"), 
                {"email": email}
            ).fetchone()

            if verificar:
                flash('E-mail já cadastrado!')
                return redirect(url_for('cadastro'))

            hashed = generate_password_hash(senha)
            inserir = text("""
                INSERT INTO Usuarios (Nome_usuario, Email, Senha, Data_inscricao, Multa_atual)
                VALUES (:nome, :email, :senha, CURDATE(), 0)
            """)
            db.execute(inserir, {"nome": nome, "email": email, "senha": hashed})
            db.commit()

            flash('Usuário cadastrado com sucesso!')
            return redirect(url_for('login'))
        finally:
            db.close()

    return render_template('cadastro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        db = Session()
        try:
            query = text("""
                SELECT ID_usuario, Nome_usuario, Email, Senha
                FROM Usuarios
                WHERE Email = :email
            """)
            user = db.execute(query, {"email": email}).fetchone()

            if not user:
                flash("E-mail não encontrado.")
                return redirect(url_for('login'))

            if not check_password_hash(user.Senha, senha):
                flash("Senha incorreta.")
                return redirect(url_for('login'))

            login_user(User(user.ID_usuario, user.Nome_usuario, user.Email))
            flash(f"Bem-vindo(a), {user.Nome_usuario}!")
            return redirect(url_for('dashboard'))
        finally:
            db.close()

    return render_template('login.html')


@app.route('/logout')   
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!')
    return redirect(url_for('index'))



def inserir_livros_padrao():
    db = Session()
    try:
        qtd = db.execute(text("SELECT COUNT(*) AS total FROM Livros")).fetchone().total
        if qtd == 0:
            livros_padrao = [
                ("Dom Casmurro", "9788535914849", 1899, 2, "Romance clássico de Machado de Assis."),
                ("1984", "9780451524935", 1949, 1, "Distopia política de George Orwell."),
                ("O Pequeno Príncipe", "9788522005233", 1943, 1, "Obra filosófica de Antoine de Saint-Exupéry."),
                ("O Alquimista", "9780061122415", 1988, 2, "Romance espiritual de Paulo Coelho."),
                ("Capitães da Areia", "9788520921313", 1937, 1, "Clássico social de Jorge Amado.")
            ]
            for titulo, isbn, ano, qtd_livro, resumo in livros_padrao:
                db.execute(text("""
                    INSERT INTO Livros (Titulo, ISBN, Ano_publicacao, Quantidade_disponivel, Resumo)
                    VALUES (:titulo, :isbn, :ano, :qtd, :resumo)
                """), {"titulo": titulo, "isbn": isbn, "ano": ano, "qtd": qtd_livro, "resumo": resumo})
            db.commit()
    finally:
        db.close()



@app.route('/dashboard')
@login_required
def dashboard():
    inserir_livros_padrao()

    db = Session()
    try:
        livros = db.execute(text("""
            SELECT ID_livro, Titulo, Ano_publicacao, Quantidade_disponivel
            FROM Livros
        """)).fetchall()

        emprestimos = db.execute(text("""
            SELECT e.ID_emprestimo, l.Titulo, e.Data_emprestimo, 
                   e.Data_devolucao_prevista, e.Status_emprestimo
            FROM Emprestimos e
            JOIN Livros l ON e.Livro_id = l.ID_livro
            WHERE e.Usuario_id = :uid
            ORDER BY e.Data_emprestimo DESC
        """), {"uid": current_user.id}).fetchall()

        autores = db.execute(text("""
            SELECT ID_autor, Nome_autor
            FROM Autores
            ORDER BY Nome_autor
        """)).fetchall()

        generos = db.execute(text("""
            SELECT ID_genero, Nome_genero
            FROM Generos
            ORDER BY Nome_genero
        """)).fetchall()

        editoras = db.execute(text("""
            SELECT ID_editora, Nome_editora
            FROM Editoras
            ORDER BY Nome_editora
        """)).fetchall()

        return render_template('dashboard.html', 
                         usuario=current_user.nome, 
                         livros=livros, 
                         emprestimos=emprestimos,
                         autores=autores,
                         generos=generos,
                         editoras=editoras)
    finally:
        db.close()



@app.route('/add_livro', methods=['POST'])
@login_required
def add_livro():
    db = Session()
    try:
        titulo = request.form['titulo']
        isbn = request.form['isbn']
        ano = request.form['ano']
        qtd = request.form['qtd']
        autor_id = request.form.get('autor_id')
        genero_id = request.form.get('genero_id')
        editora_id = request.form.get('editora_id')

        existe = db.execute(
            text("SELECT ID_livro FROM Livros WHERE ISBN = :isbn"),
            {"isbn": isbn}
        ).fetchone()

        if existe:
            flash('ISBN já cadastrado!')
            return redirect(url_for('dashboard'))

        query = text("""
            INSERT INTO Livros (Titulo, ISBN, Ano_publicacao, Quantidade_disponivel, Autor_id, Genero_id, Editora_id, Resumo, Usuario_id)
            VALUES (:titulo, :isbn, :ano, :qtd, :autor_id, :genero_id, :editora_id, :resumo, :uid)
        """)
        db.execute(query, {
            "titulo": titulo,
            "isbn": isbn,
            "ano": int(ano) if ano else None,
            "qtd": int(qtd) if qtd else 0,
            "resumo": request.form.get('resumo', None),
            "autor_id": int(autor_id) if autor_id else None,
            "genero_id": int(genero_id) if genero_id else None,
            "editora_id": int(editora_id) if editora_id else None,
            "uid": current_user.id
        })

        db.commit()
        flash('Livro adicionado com sucesso!')
    except Exception as e:
        flash(f'Erro ao adicionar livro: {str(e)}')
    finally:
        db.close()
    
    return redirect(url_for('dashboard'))


@app.route('/editar_livro/<int:id_livro>', methods=['GET', 'POST'])
@login_required
def editar_livro(id_livro):
    db = Session()
    
    try:
        if request.method == 'POST':
            novo_titulo = request.form['titulo']
            novo_isbn = request.form['isbn']
            novo_ano = request.form['ano']
            nova_qtd = request.form['qtd']
            novo_resumo = request.form.get('resumo', '')
            novo_genero = request.form.get('genero_id')
            novo_autor = request.form.get('autor_id')
            novo_editora = request.form.get('editora_id')

            db.execute(text("""
                UPDATE Livros
                SET Titulo = :titulo,
                    ISBN = :isbn,
                    Ano_publicacao = :ano,
                    Quantidade_disponivel = :qtd,
                    Resumo = :resumo,
                    Genero_id = :genero,
                    Autor_id = :autor,
                    Editora_id = :editora
                WHERE ID_livro = :id
            """), {
                "titulo": novo_titulo,
                "isbn": novo_isbn,
                "ano": int(novo_ano) if novo_ano else None,
                "qtd": int(nova_qtd) if nova_qtd else 0,
                "resumo": novo_resumo,
                "genero": int(novo_genero) if novo_genero else None,
                "autor": int(novo_autor) if novo_autor else None,
                "editora": int(novo_editora) if novo_editora else None,
                "id": id_livro
            })

            db.commit()
            flash('Livro atualizado com sucesso!')
            return redirect(url_for('dashboard'))

        livro = db.execute(
            text("SELECT * FROM Livros WHERE ID_livro = :id"), 
            {"id": id_livro}
        ).fetchone()

        if not livro:
            flash('Livro não encontrado.')
            return redirect(url_for('dashboard'))

        # opcional: enviar lista de generos/autores/editoras para o form de edição
        generos = db.execute(text("SELECT ID_genero, Nome_genero FROM Generos ORDER BY Nome_genero")).fetchall()
        autores = db.execute(text("SELECT ID_autor, Nome_autor FROM Autores ORDER BY Nome_autor")).fetchall()
        editoras = db.execute(text("SELECT ID_editora, Nome_editora FROM Editoras ORDER BY Nome_editora")).fetchall()

        return render_template('editar.html', livro=livro, generos=generos, autores=autores, editoras=editoras)
    finally:
        db.close()


@app.route('/remover_livro/<int:id_livro>', methods=['POST'])
@login_required
def remover_livro(id_livro):
    db = Session()
    try:
        livro = db.execute(text("""
            SELECT Usuario_id FROM Livros WHERE ID_livro = :id
        """), {"id": id_livro}).fetchone()

        if not livro:
            flash("Livro não encontrado.")
            return redirect(url_for('dashboard'))

        if livro.Usuario_id and livro.Usuario_id != current_user.id:
            flash("Você só pode remover livros que você mesmo adicionou.")
            return redirect(url_for('dashboard'))

        # Impedir remoção se houver qualquer empréstimo (histórico ou ativo)
        emprestimos_total = db.execute(text("""
            SELECT COUNT(*) AS total
            FROM Emprestimos
            WHERE Livro_id = :id
        """), {"id": id_livro}).fetchone()

        if emprestimos_total.total > 0:
            flash("Não é possível remover este livro, pois existem registros de empréstimos associados. Para preservar o histórico, remova ou ajuste os empréstimos antes.")
            return redirect(url_for('dashboard'))

        db.execute(text("DELETE FROM Livros WHERE ID_livro = :id"), {"id": id_livro})
        db.commit()

        flash("Livro removido com sucesso!")
    except Exception as e:
        flash(f"Erro ao remover livro: {str(e)}")
    finally:
        db.close()
    
    return redirect(url_for('dashboard'))

@app.route('/add_genero', methods=['GET', 'POST'])
@login_required
def add_genero():
    db = Session()
    
    try:
        if request.method == 'POST':
            nome = request.form['nome_genero']

            db.execute(text("""
                INSERT INTO Generos (Nome_genero)
                VALUES (:nome)
            """), {
                "nome": nome,
                "uid": current_user.id
            })

            db.commit()
            flash('Gênero adicionado com sucesso!')
            return redirect(url_for('add_genero'))

        generos = db.execute(text("""
            SELECT ID_genero, Nome_genero
            FROM Generos
            ORDER BY Nome_genero
        """)).fetchall()

        return render_template('add_genero.html', usuario=current_user.nome, generos=generos)
    finally:
        db.close()


@app.route('/editar_genero/<int:id_genero>', methods=['GET', 'POST'])
@login_required
def editar_genero(id_genero):
    db = Session()
    try:
        genero = db.execute(
            text("SELECT * FROM Generos WHERE ID_genero = :id"),
            {"id": id_genero}
        ).fetchone()

        if not genero:
            flash("Gênero não encontrado.")
            return redirect(url_for('add_genero'))

        if request.method == 'POST':
            nome = request.form.get('nome_genero', '').strip()
            db.execute(text("""
                UPDATE Generos
                SET Nome_genero = :nome
                WHERE ID_genero = :id
            """), {"nome": nome, "id": id_genero})
            db.commit()
            flash("Gênero atualizado com sucesso!")
            return redirect(url_for('add_genero'))

        return render_template('editar_genero.html', usuario=current_user.nome, genero=genero)
    finally:
        db.close()

@app.route('/remover_genero/<int:id_genero>', methods=['POST'])
@login_required
def remover_genero(id_genero):
    db = Session()
    try:
        genero = db.execute(text("""
            SELECT * FROM Generos WHERE ID_genero = :id
        """), {"id": id_genero}).fetchone()

        if not genero:
            flash("Gênero não encontrado.")
            return redirect(url_for('add_genero'))

        # Verifica livros vinculados ao gênero (ligações atuais)
        livros_vinculados = db.execute(text("""
            SELECT COUNT(*) AS total FROM Livros WHERE Genero_id = :id
        """), {"id": id_genero}).fetchone()

        if livros_vinculados.total > 0:
            flash("Não é possível remover este gênero, pois há livros associados a ele.")
            return redirect(url_for('add_genero'))

        # Verifica empréstimos vinculados a livros desse gênero pelo snapshot salvo no momento do empréstimo
        emprestimos_snapshot = db.execute(text("""
            SELECT COUNT(*) AS total FROM Emprestimos WHERE Livro_genero_id = :id
        """), {"id": id_genero}).fetchone()

        if emprestimos_snapshot.total > 0:
            flash("Não é possível remover este gênero; existem empréstimos históricos vinculados a ele.")
            return redirect(url_for('add_genero'))

        # Verifica empréstimos que referenciam livros cujo gênero atual é o que será removido
        emprestimos_vinculados = db.execute(text("""
            SELECT COUNT(*) AS total
            FROM Emprestimos e
            JOIN Livros l ON e.Livro_id = l.ID_livro
            WHERE l.Genero_id = :id
        """), {"id": id_genero}).fetchone()

        if emprestimos_vinculados.total > 0:
            flash("Não é possível remover este gênero, pois existem empréstimos relacionados a livros deste gênero.")
            return redirect(url_for('add_genero'))

        db.execute(text("DELETE FROM Generos WHERE ID_genero = :id"), {"id": id_genero})
        db.commit()

        flash("Gênero removido com sucesso!")
    except Exception as e:
        flash(f"Erro ao remover gênero: {str(e)}")
    finally:
        db.close()

    return redirect(url_for('add_genero'))



@app.route('/add_autor', methods=['GET', 'POST'])
@login_required
def add_autor():
    db = Session()
    
    try:
        if request.method == 'POST':
            nome = request.form['nome_autor']
            nacionalidade = request.form.get('nacionalidade', '')
            data_nascimento = request.form.get('data_nascimento', None)
            biografia = request.form.get('biografia', '')

            db.execute(text("""
                INSERT INTO Autores (Nome_autor, Nacionalidade, Data_nascimento, Biografia, Usuario_id)
                VALUES (:nome, :nacionalidade, :data_nasc, :bio, :uid)
            """), {
                "nome": nome,
                "nacionalidade": nacionalidade if nacionalidade else None,
                "data_nasc": data_nascimento if data_nascimento else None,
                "bio": biografia if biografia else None,
                "uid": current_user.id
            })

            db.commit()
            flash('Autor adicionado com sucesso!')
            return redirect(url_for('add_autor'))

        autores = db.execute(text("""
            SELECT ID_autor, Nome_autor, Nacionalidade, Usuario_id
            FROM Autores
            ORDER BY Nome_autor
        """)).fetchall()

        return render_template('add_autor.html', usuario=current_user.nome, autores=autores)
    finally:
        db.close()


@app.route('/remover_autor/<int:id_autor>', methods=['POST'])
@login_required
def remover_autor(id_autor):
    db = Session()
    try:
        autor = db.execute(text("""
            SELECT Usuario_id FROM Autores WHERE ID_autor = :id
        """), {"id": id_autor}).fetchone()

        if not autor:
            flash("Autor não encontrado.")
            return redirect(url_for('add_autor'))

        if autor.Usuario_id != current_user.id:
            flash("Você só pode remover autores que você mesmo adicionou.")
            return redirect(url_for('add_autor'))

        # Verifica livros do autor
        livros = db.execute(text("""
            SELECT COUNT(*) AS total FROM Livros WHERE Autor_id = :id
        """), {"id": id_autor}).fetchone()

        if livros.total > 0:
            flash("Não é possível remover este autor, pois há livros associados.")
            return redirect(url_for('add_autor'))

        # Verifica empréstimos vinculados a livros desse autor (caso haja inconsistências)
        emprestimos_vinculados = db.execute(text("""
            SELECT COUNT(*) AS total
            FROM Emprestimos e
            JOIN Livros l ON e.Livro_id = l.ID_livro
            WHERE l.Autor_id = :id
        """), {"id": id_autor}).fetchone()

        if emprestimos_vinculados.total > 0:
            flash("Não é possível remover este autor, pois existem empréstimos relacionados a livros deste autor.")
            return redirect(url_for('add_autor'))

        db.execute(text("DELETE FROM Autores WHERE ID_autor = :id"), {"id": id_autor})
        db.commit()

        flash("Autor removido com sucesso!")
    except Exception as e:
        flash(f"Erro ao remover autor: {str(e)}")
    finally:
        db.close()
    
    return redirect(url_for('add_autor'))



@app.route('/editar_autor/<int:id_autor>', methods=['GET', 'POST'])
@login_required
def editar_autor(id_autor):
    db = Session()
    try:
        autor = db.execute(
            text("SELECT * FROM Autores WHERE ID_autor = :id"),
            {"id": id_autor}
        ).fetchone()

        if not autor:
            flash("Autor não encontrado.")
            return redirect(url_for('add_autor'))

        if autor.Usuario_id != current_user.id:
            flash("Você só pode editar autores que você mesmo adicionou.")
            return redirect(url_for('add_autor'))

        if request.method == 'POST':
            nome = request.form.get('nome_autor', '').strip()
            nacionalidade = request.form.get('nacionalidade', '').strip()
            data_nascimento = request.form.get('data_nascimento', None)
            biografia = request.form.get('biografia', '').strip()

            db.execute(text("""
                UPDATE Autores
                SET Nome_autor = :nome,
                    Nacionalidade = :nacionalidade,
                    Data_nascimento = :data_nasc,
                    Biografia = :bio
                WHERE ID_autor = :id
            """), {
                "nome": nome,
                "nacionalidade": nacionalidade if nacionalidade else None,
                "data_nasc": data_nascimento if data_nascimento else None,
                "bio": biografia if biografia else None,
                "id": id_autor
            })
            db.commit()
            flash("Autor atualizado com sucesso!")
            return redirect(url_for('add_autor'))

        autores = db.execute(text("""
            SELECT ID_autor, Nome_autor, Nacionalidade, Usuario_id
            FROM Autores
            ORDER BY Nome_autor
        """)).fetchall()

        return render_template('edit_autor.html', usuario=current_user.nome, autor=autor, autores=autores)
    finally:
        db.close()


@app.route('/emprestar/<int:id_livro>', methods=['POST'])
@login_required
def emprestar_livro(id_livro):
    db = Session()
    try:
        # pega quantidade e snapshot de autor/gênero
        livro = db.execute(text("""
            SELECT Quantidade_disponivel, Autor_id, Genero_id
            FROM Livros
            WHERE ID_livro = :id
        """), {"id": id_livro}).fetchone()

        if not livro:
            flash("Livro não encontrado.")
            return redirect(url_for('dashboard'))

        if livro.Quantidade_disponivel <= 0:
            flash("Livro indisponível para empréstimo.")
            return redirect(url_for('dashboard'))

        # Cria o empréstimo salvando snapshot de autor e gênero
        db.execute(text("""
            INSERT INTO Emprestimos (Usuario_id, Livro_id, Data_emprestimo, 
                                     Data_devolucao_prevista, Status_emprestimo, Livro_genero_id, Livro_autor_id)
            VALUES (:uid, :lid, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'pendente', :gen_id, :aut_id)
        """), {
            "uid": current_user.id,
            "lid": id_livro,
            "gen_id": livro.Genero_id,
            "aut_id": livro.Autor_id
        })

        db.execute(text("""
            UPDATE Livros 
            SET Quantidade_disponivel = Quantidade_disponivel - 1 
            WHERE ID_livro = :id
        """), {"id": id_livro})

        db.commit()
        flash("Empréstimo realizado com sucesso!")
    except Exception as e:
        flash(f"Erro ao realizar empréstimo: {str(e)}")
    finally:
        db.close()
    
    return redirect(url_for('dashboard'))


@app.route('/devolver/<int:id_emprestimo>', methods=['POST'])
@login_required
def devolver_livro(id_emprestimo):
    db = Session()
    try:
        emprestimo = db.execute(text("""
            SELECT Livro_id FROM Emprestimos
            WHERE ID_emprestimo = :eid 
              AND Usuario_id = :uid 
              AND Status_emprestimo = 'pendente'
        """), {"eid": id_emprestimo, "uid": current_user.id}).fetchone()

        if not emprestimo:
            flash("Empréstimo inválido ou já devolvido.")
            return redirect(url_for('dashboard'))

        db.execute(text("""
            UPDATE Emprestimos
            SET Status_emprestimo = 'devolvido', Data_devolucao_real = CURDATE()
            WHERE ID_emprestimo = :eid
        """), {"eid": id_emprestimo})

        db.execute(text("""
            UPDATE Livros
            SET Quantidade_disponivel = Quantidade_disponivel + 1
            WHERE ID_livro = :lid
        """), {"lid": emprestimo.Livro_id})

        db.commit()
        flash("Livro devolvido com sucesso!")
    except Exception as e:
        flash(f"Erro ao devolver livro: {str(e)}")
    finally:
        db.close()
    
    return redirect(url_for('dashboard'))


@app.route('/add_editora', methods=['GET', 'POST'])
@login_required
def add_editora():
    db = Session()
    
    try:
        if request.method == 'POST':
            nome = request.form['nome_editora']
            endereco = request.form.get('endereco_editora', None)

            db.execute(text("""
                INSERT INTO Editoras (Nome_editora, Endereco_editora, Usuario_id)
                VALUES (:nome, :endereco, :uid)
            """), {
                "nome": nome,
                "endereco": endereco if endereco else None,
                "uid": current_user.id
            })

            db.commit()
            flash('Editora adicionada com sucesso!')
            return redirect(url_for('add_editora'))

        editoras = db.execute(text("""
            SELECT ID_editora, Nome_editora, Endereco_editora, Usuario_id
            FROM Editoras
            ORDER BY Nome_editora
        """)).fetchall()

        return render_template('add_editora.html', usuario=current_user.nome, editoras=editoras)
    finally:
        db.close()


@app.route('/editar_editora/<int:id_editora>', methods=['GET', 'POST'])
@login_required
def editar_editora(id_editora):
    db = Session()
    try:
        editora = db.execute(
            text("SELECT * FROM Editoras WHERE ID_editora = :id"),
            {"id": id_editora}
        ).fetchone()

        if not editora:
            flash("Editora não encontrada.")
            return redirect(url_for('add_editora'))

        if request.method == 'POST':
            nome = request.form.get('nome_editora', '').strip()
            endereco = request.form.get('endereco_editora', '').strip()
            db.execute(text("""
                UPDATE Editoras
                SET Nome_editora = :nome,
                    Endereco_editora = :end
                WHERE ID_editora = :id
            """), {"nome": nome, "end": endereco if endereco else None, "id": id_editora})
            db.commit()
            flash("Editora atualizada com sucesso!")
            return redirect(url_for('add_editora'))

        return render_template('editar_editora.html', usuario=current_user.nome, editora=editora)
    finally:
        db.close()


@app.route('/remover_editora/<int:id_editora>', methods=['POST'])
@login_required
def remover_editora(id_editora):
    db = Session()
    try:
        editora = db.execute(text("""
            SELECT * FROM Editoras WHERE ID_editora = :id
        """), {"id": id_editora}).fetchone()

        if not editora:
            flash("Editora não encontrada.")
            return redirect(url_for('add_editora'))

        # Verifica se a editora está vinculada a algum livro
        livros_vinculados = db.execute(text("""
            SELECT COUNT(*) AS total FROM Livros WHERE Editora_id = :id
        """), {"id": id_editora}).fetchone()

        if livros_vinculados.total > 0:
            flash("Não é possível remover esta editora, pois há livros associados a ela.")
            return redirect(url_for('add_editora'))

        db.execute(text("DELETE FROM Editoras WHERE ID_editora = :id"), {"id": id_editora})
        db.commit()

        flash("Editora removida com sucesso!")
    except Exception as e:
        flash(f"Erro ao remover editora: {str(e)}")
    finally:
        db.close()

    return redirect(url_for('add_editora'))


if __name__ == '__main__':
    app.run(debug=True)
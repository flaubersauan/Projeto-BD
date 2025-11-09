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
    query = text("SELECT ID_usuario, Nome_usuario, Email FROM Usuarios WHERE ID_usuario = :id")
    result = db.execute(query, {"id": user_id}).fetchone()
    db.close()

    if result:
        return User(id=result.ID_usuario, nome=result.Nome_usuario, email=result.Email)
    return None


# Página inicial
@app.route('/')
def index():
    return render_template('index.html')


# Cadastro de usuário
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        db = Session()
        verificar = db.execute(text("SELECT * FROM Usuarios WHERE Email = :email"), {"email": email}).fetchone()

        if verificar:
            flash('E-mail já cadastrado!')
            db.close()
            return redirect(url_for('cadastro'))

        hashed = generate_password_hash(senha)
        inserir = text("""
            INSERT INTO Usuarios (Nome_usuario, Email, Senha, Data_inscricao, Multa_atual)
            VALUES (:nome, :email, :senha, CURDATE(), 0)
        """)
        db.execute(inserir, {"nome": nome, "email": email, "senha": hashed})
        db.commit()
        db.close()

        flash('Usuário cadastrado com sucesso!')
        return redirect(url_for('login'))

    return render_template('cadastro.html')


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        db = Session()
        query = text("""
            SELECT ID_usuario, Nome_usuario, Email, Senha
            FROM Usuarios
            WHERE Email = :email
        """)
        user = db.execute(query, {"email": email}).fetchone()
        db.close()

        if not user:
            flash("E-mail não encontrado.")
            return redirect(url_for('login'))

        if not check_password_hash(user.Senha, senha):
            flash("Senha incorreta.")
            return redirect(url_for('login'))

        login_user(User(user.ID_usuario, user.Nome_usuario, user.Email))
        flash(f"Bem-vindo(a), {user.Nome_usuario}!")
        return redirect(url_for('dashboard'))

    return render_template('login.html')


# ---------- NOVO: Função para inserir livros padrão ----------
def inserir_livros_padrao():
    db = Session()
    # Verifica se há livros
    qtd = db.execute(text("SELECT COUNT(*) AS total FROM Livros")).fetchone().total
    if qtd == 0:
        livros_padrao = [
            ("Dom Casmurro", "9788535914849", 1899, 2, "Romance clássico de Machado de Assis."),
            ("1984", "9780451524935", 1949, 1, "Distopia política de George Orwell."),
            ("O Pequeno Príncipe", "9788522005233", 1943, 1, "Obra filosófica de Antoine de Saint-Exupéry."),
            ("O Alquimista", "9780061122415", 1988, 2, "Romance espiritual de Paulo Coelho."),
            ("Capitães da Areia", "9788520921313", 1937, 1, "Clássico social de Jorge Amado.")
        ]
        for titulo, isbn, ano, qtd, resumo in livros_padrao:
            db.execute(text("""
                INSERT INTO Livros (Titulo, ISBN, Ano_publicacao, Quantidade_disponivel, Resumo)
                VALUES (:titulo, :isbn, :ano, :qtd, :resumo)
            """), {"titulo": titulo, "isbn": isbn, "ano": ano, "qtd": qtd, "resumo": resumo})
        db.commit()
    db.close()


# Dashboard (catálogo de livros e empréstimos)
@app.route('/dashboard')
@login_required
def dashboard():
    inserir_livros_padrao()  # Garante que existam livros iniciais

    db = Session()
    # Lista todos os livros disponíveis
    livros = db.execute(text("""
        SELECT ID_livro, Titulo, Ano_publicacao, Quantidade_disponivel
        FROM Livros
    """)).fetchall()

    # Lista empréstimos do usuário logado
    emprestimos = db.execute(text("""
        SELECT e.ID_emprestimo, l.Titulo, e.Data_emprestimo, e.Data_devolucao_prevista, e.Status_emprestimo
        FROM Emprestimos e
        JOIN Livros l ON e.Livro_id = l.ID_livro
        WHERE e.Usuario_id = :uid
    """), {"uid": current_user.id}).fetchall()

    db.close()
    return render_template('dashboard.html', usuario=current_user.nome, livros=livros, emprestimos=emprestimos)


# Rota para pegar um livro emprestado
@app.route('/emprestar/<int:id_livro>', methods=['POST'])
@login_required
def emprestar_livro(id_livro):
    db = Session()

    # Verifica se o livro existe e está disponível
    livro = db.execute(text("SELECT Quantidade_disponivel FROM Livros WHERE ID_livro = :id"),
                       {"id": id_livro}).fetchone()

    if not livro:
        flash("Livro não encontrado.")
        db.close()
        return redirect(url_for('dashboard'))

    if livro.Quantidade_disponivel <= 0:
        flash("Livro indisponível para empréstimo.")
        db.close()
        return redirect(url_for('dashboard'))

    # Cria o empréstimo
    db.execute(text("""
        INSERT INTO Emprestimos (Usuario_id, Livro_id, Data_emprestimo, Data_devolucao_prevista, Status_emprestimo)
        VALUES (:uid, :lid, CURDATE(), DATE_ADD(CURDATE(), INTERVAL 7 DAY), 'pendente')
    """), {"uid": current_user.id, "lid": id_livro})

    # Atualiza quantidade disponível
    db.execute(text("""
        UPDATE Livros SET Quantidade_disponivel = Quantidade_disponivel - 1 WHERE ID_livro = :id
    """), {"id": id_livro})

    db.commit()
    db.close()
    flash("Empréstimo realizado com sucesso!")
    return redirect(url_for('dashboard'))


# Rota para devolver um livro
@app.route('/devolver/<int:id_emprestimo>', methods=['POST'])
@login_required
def devolver_livro(id_emprestimo):
    db = Session()

    # Busca o livro do empréstimo
    emprestimo = db.execute(text("""
        SELECT Livro_id FROM Emprestimos
        WHERE ID_emprestimo = :eid AND Usuario_id = :uid AND Status_emprestimo = 'pendente'
    """), {"eid": id_emprestimo, "uid": current_user.id}).fetchone()

    if not emprestimo:
        flash("Empréstimo inválido ou já devolvido.")
        db.close()
        return redirect(url_for('dashboard'))

    # Atualiza status e devolução
    db.execute(text("""
        UPDATE Emprestimos
        SET Status_emprestimo = 'devolvido', Data_devolucao_real = CURDATE()
        WHERE ID_emprestimo = :eid
    """), {"eid": id_emprestimo})

    # Devolve livro ao estoque
    db.execute(text("""
        UPDATE Livros
        SET Quantidade_disponivel = Quantidade_disponivel + 1
        WHERE ID_livro = :lid
    """), {"lid": emprestimo.Livro_id})

    db.commit()
    db.close()
    flash("Livro devolvido com sucesso!")
    return redirect(url_for('dashboard'))


# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)

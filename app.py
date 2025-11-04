from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from database import Session

app = Flask(__name__)
app.secret_key = "segredo_muito_seguro"

# Configura o Flask-Login
login_manager = LoginManager(app)
login_manager.login_view = 'login'


# Classe UserMixin (para compatibilidade com Flask-Login)
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


# Cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']

        db = Session()
        # Verifica se já existe e-mail
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
        # Busca também o campo Senha agora
        query = text("""
            SELECT ID_usuario, Nome_usuario, Email, Senha
            FROM Usuarios
            WHERE Email = :email
        """)
        user = db.execute(query, {"email": email}).fetchone()
        db.close()

        # Verifica se o usuário existe
        if not user:
            flash("E-mail não encontrado.")
            return redirect(url_for('login'))

        # Valida a senha com o hash salvo no banco
        if not check_password_hash(user.Senha, senha):
            flash("Senha incorreta.")
            return redirect(url_for('login'))

        # Login bem-sucedido
        login_user(User(user.ID_usuario, user.Nome_usuario, user.Email))
        flash(f"Bem-vindo(a), {user.Nome_usuario}!")
        return redirect(url_for('dashboard'))

    return render_template('login.html')

# Dashboard com listagem e inserção de livros
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    db = Session()

    if request.method == 'POST':
        titulo = request.form['titulo']
        isbn = request.form['isbn']
        ano = request.form['ano']

        query = text("""
            INSERT INTO Livros (Titulo, ISBN, Ano_publicacao, Quantidade_disponivel)
            VALUES (:titulo, :isbn, :ano, 10)
        """)
        db.execute(query, {"titulo": titulo, "isbn": isbn, "ano": ano})
        db.commit()
        flash('Livro adicionado com sucesso!')

    # Lista os livros
    livros = db.execute(text("SELECT ID_livro, Titulo, Ano_publicacao FROM Livros")).fetchall()
    db.close()

    return render_template('dashboard.html', usuario=current_user.nome, livros=livros)


# Remover livro
@app.route('/remover_livro/<int:id_livro>', methods=['POST'])
@login_required
def remover_livro(id_livro):
    db = Session()
    db.execute(text("DELETE FROM Livros WHERE ID_livro = :id"), {"id": id_livro})
    db.commit()
    db.close()
    flash('Livro removido com sucesso!')
    return redirect(url_for('dashboard'))


# Editar livro
@app.route('/editar_livro/<int:id_livro>', methods=['POST'])
@login_required
def editar_livro(id_livro):
    novo_titulo = request.form['novo_titulo']
    db = Session()
    db.execute(text("UPDATE Livros SET Titulo = :titulo WHERE ID_livro = :id"),
               {"titulo": novo_titulo, "id": id_livro})
    db.commit()
    db.close()
    flash('Livro atualizado com sucesso!')
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

import os
from datetime import datetime
from functools import wraps

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    flash
)

from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from models import db, Usuario, Produto, Categoria


# ============================================================
# CONFIGURAÇÃO
# ============================================================

app = Flask(__name__)

# Chave secreta:
# Em produção, será lida da variável de ambiente SECRET_KEY.
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "chave-temporaria-musubi"
)

# Banco SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///musubi.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Pasta de uploads
app.config["UPLOAD_FOLDER"] = os.path.join(
    "static",
    "assets",
    "img",
    "produtos"
)

# Tamanho máximo de upload: 5 MB
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024


# Extensões de imagem permitidas
EXTENSOES_PERMITIDAS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}


# Inicializa banco
db.init_app(app)


# ============================================================
# DADOS INICIAIS
# ============================================================

def seed_produtos():
    """
    Popula a loja com produtos de exemplo
    caso o banco esteja vazio.
    """

    if Produto.query.count() > 0:
        return

    produtos_iniciais = [

        Produto(
            nome="Vaso Decorativo Folhas",
            preco=59.99,
            descricao=(
                "Vaso de cerâmica artesanal com estampa "
                "de folhas, feito à mão."
            ),
            imagem="assets/img/vaso.jpg"
        ),

        Produto(
            nome="Kit Cerâmica Artesanal",
            preco=99.99,
            descricao=(
                "Conjunto de peças de cerâmica artesanal "
                "para decoração."
            ),
            imagem="assets/img/kit-ceramica.jpg"
        ),

        Produto(
            nome="Quadro Porsche GT3",
            preco=79.99,
            descricao=(
                "Conjunto de quadros decorativos com "
                "ilustração minimalista."
            ),
            imagem="assets/img/porche.jpg"
        ),

        Produto(
            nome="Quadro Ferrari",
            preco=49.99,
            descricao=(
                "Quadro decorativo para complementar "
                "a decoração do ambiente."
            ),
            imagem="assets/img/quadro-ferrari.jpg"
        ),

        Produto(
            nome="Prato Decorativo Coelhinhos",
            preco=39.99,
            descricao=(
                "Prato de porcelana pintado à mão, ideal "
                "para decoração ou uso especial."
            ),
            imagem="assets/img/prato.jpg"
        ),

        Produto(
            nome="Conjunto de Cama Estampado",
            preco=189.99,
            descricao=(
                "Jogo de cama macio com estampa "
                "exclusiva Musubi."
            ),
            imagem="assets/img/conjuntoCama.jpg"
        ),

        Produto(
            nome="Cesta de Presente Musubi",
            preco=129.99,
            descricao=(
                "Cesta especial com itens selecionados, "
                "perfeita para presentear."
            ),
            imagem="assets/img/presente.jpg"
        )
    ]

    db.session.add_all(produtos_iniciais)
    db.session.commit()


def seed_categorias():
    """
    Cria categorias iniciais caso o banco esteja vazio.
    """

    if Categoria.query.count() > 0:
        return

    categorias_iniciais = [
        Categoria(nome="Cerâmicas"),
        Categoria(nome="Quadros"),
        Categoria(nome="Presentes"),
        Categoria(nome="Pratos")
    ]

    db.session.add_all(categorias_iniciais)
    db.session.commit()


def seed_admin():
    """
    Cria um administrador padrão caso ainda não exista.
    """

    if Usuario.query.filter_by(
        email="admin@musubi.com"
    ).first():
        return

    admin = Usuario(
        nome="Administrador Musubi",
        email="admin@musubi.com",
        senha=generate_password_hash("admin123"),
        is_admin=True
    )

    db.session.add(admin)
    db.session.commit()


# ============================================================
# CRIAÇÃO DO BANCO
# ============================================================

with app.app_context():

    db.create_all()

    seed_categorias()
    seed_produtos()
    seed_admin()


# ============================================================
# CARRINHO
# ============================================================

def get_carrinho():
    """
    Retorna o carrinho da sessão.
    Formato:

    {
        "produto_id": quantidade
    }
    """

    return session.get("carrinho", {})


def salvar_carrinho(carrinho):

    session["carrinho"] = carrinho
    session.modified = True


# ============================================================
# DADOS GLOBAIS
# ============================================================

@app.context_processor
def dados_globais():

    carrinho = get_carrinho()

    total_itens = (
        sum(carrinho.values())
        if carrinho
        else 0
    )

    usuario_logado = None

    if session.get("usuario"):

        usuario_logado = Usuario.query.get(
            session["usuario"]
        )

    return {
        "cart_count": total_itens,
        "usuario_logado": usuario_logado
    }


# ============================================================
# AUTENTICAÇÃO
# ============================================================

def login_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if not session.get("usuario"):

            flash(
                "Você precisa estar logado para adicionar produtos ao carrinho."
            )

            return redirect(
                url_for(
                    "login",
                    next=request.path
                )
            )

        return f(*args, **kwargs)

    return decorated


def admin_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if not session.get("usuario"):

            flash(
                "Você precisa estar logado para acessar o painel administrativo."
            )

            return redirect(
                url_for(
                    "login",
                    next=request.path
                )
            )

        usuario = Usuario.query.get(
            session["usuario"]
        )

        if not usuario or not usuario.is_admin:

            flash(
                "Acesso restrito a administradores."
            )

            return redirect(
                url_for("home")
            )

        return f(*args, **kwargs)

    return decorated


# ============================================================
# PÁGINAS INSTITUCIONAIS
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        active="inicio"
    )


@app.route("/consultoria")
def consultoria():

    return render_template(
        "consultoria.html",
        active="servicos"
    )


@app.route("/projeto")
def projeto():

    return render_template(
        "projeto.html",
        active="servicos"
    )


@app.route("/acessoria")
def acessoria():

    return render_template(
        "acessoria.html",
        active="servicos"
    )


# ============================================================
# LOJA
# ============================================================

@app.route("/loja")
def loja():

    busca = request.args.get(
        "q",
        ""
    ).strip()

    query = Produto.query

    if busca:

        query = query.filter(
            Produto.nome.ilike(
                f"%{busca}%"
            )
        )

    produtos = query.all()

    return render_template(
        "loja.html",
        produtos=produtos,
        busca=busca,
        active="loja"
    )


@app.route("/produto/<int:id>")
def produto_detalhes(id):

    produto = Produto.query.get_or_404(id)

    return render_template(
        "produto_detalhes.html",
        produto=produto,
        active="loja"
    )


# ============================================================
# CADASTRO
# ============================================================

@app.route(
    "/cadastro",
    methods=["GET", "POST"]
)
def cadastro():

    if request.method == "POST":

        nome = (
            f"{request.form.get('nome', '').strip()} "
            f"{request.form.get('sobrenome', '').strip()}"
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        confirmar_senha = request.form.get(
            "confirmar_senha",
            ""
        )

        erro = None

        if not nome or not email or not senha:

            erro = (
                "Preencha todos os campos obrigatórios."
            )

        elif senha != confirmar_senha:

            erro = (
                "As senhas não coincidem."
            )

        elif Usuario.query.filter_by(
            email=email
        ).first():

            erro = (
                "Já existe uma conta cadastrada com esse e-mail."
            )

        if erro:

            return render_template(
                "cadastro.html",
                erro=erro
            )

        usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(
                senha
            )
        )

        db.session.add(usuario)
        db.session.commit()

        session["usuario"] = usuario.id

        return redirect(
            url_for("home")
        )

    return render_template(
        "cadastro.html"
    )


# ============================================================
# LOGIN
# ============================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        senha = request.form.get(
            "senha",
            ""
        )

        usuario = Usuario.query.filter_by(
            email=email
        ).first()

        if usuario and check_password_hash(
            usuario.senha,
            senha
        ):

            session["usuario"] = usuario.id

            return redirect(
                url_for("home")
            )

        return render_template(
            "login.html",
            erro="E-mail ou senha inválidos."
        )

    return render_template(
        "login.html"
    )


# ============================================================
# LOGOUT
# ============================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("home")
    )


# ============================================================
# CARRINHO
# ============================================================

@app.route(
    "/carrinho/adicionar/<int:id>"
)
@login_required
def adicionar(id):

    produto = Produto.query.get_or_404(id)

    carrinho = get_carrinho()

    chave = str(
        produto.id
    )

    carrinho[chave] = (
        carrinho.get(chave, 0) + 1
    )

    salvar_carrinho(carrinho)

    destino = (
        request.referrer
        or url_for("loja")
    )

    return redirect(destino)


@app.route(
    "/carrinho/aumentar/<int:id>"
)
def aumentar(id):

    carrinho = get_carrinho()

    chave = str(id)

    carrinho[chave] = (
        carrinho.get(chave, 0) + 1
    )

    salvar_carrinho(carrinho)

    return redirect(
        url_for("carrinho")
    )


@app.route(
    "/carrinho/diminuir/<int:id>"
)
def diminuir(id):

    carrinho = get_carrinho()

    chave = str(id)

    if chave in carrinho:

        carrinho[chave] -= 1

        if carrinho[chave] <= 0:

            del carrinho[chave]

    salvar_carrinho(carrinho)

    return redirect(
        url_for("carrinho")
    )


@app.route(
    "/carrinho/remover/<int:id>"
)
def remover(id):

    carrinho = get_carrinho()

    carrinho.pop(
        str(id),
        None
    )

    salvar_carrinho(carrinho)

    return redirect(
        url_for("carrinho")
    )


@app.route("/carrinho/limpar")
def limpar_carrinho():

    salvar_carrinho({})

    return redirect(
        url_for("carrinho")
    )


@app.route("/carrinho")
def carrinho():

    carrinho_sessao = get_carrinho()

    ids = [
        int(i)
        for i in carrinho_sessao.keys()
    ]

    produtos = (
        Produto.query
        .filter(Produto.id.in_(ids))
        .all()
        if ids
        else []
    )

    itens = []

    total = 0.0

    for produto in produtos:

        quantidade = carrinho_sessao.get(
            str(produto.id),
            0
        )

        subtotal = (
            produto.preco * quantidade
        )

        total += subtotal

        itens.append({
            "produto": produto,
            "quantidade": quantidade,
            "subtotal": subtotal
        })

    return render_template(
        "carrinho.html",
        itens=itens,
        total=total,
        active="loja"
    )


# ============================================================
# ADMINISTRAÇÃO
# ============================================================

def imagem_permitida(nome_arquivo):

    return (
        "." in nome_arquivo
        and
        nome_arquivo.rsplit(
            ".",
            1
        )[1].lower()
        in EXTENSOES_PERMITIDAS
    )


# ============================================================
# DASHBOARD
# ============================================================

@app.route("/admin")
@admin_required
def admin_dashboard():

    produtos = (
        Produto.query
        .order_by(
            Produto.id.desc()
        )
        .all()
    )

    categorias = (
        Categoria.query
        .order_by(
            Categoria.nome
        )
        .all()
    )

    return render_template(
        "admin_dashboard.html",
        produtos=produtos,
        categorias=categorias
    )


# ============================================================
# CATEGORIAS - CRIAR
# ============================================================

@app.route(
    "/admin/categorias/nova",
    methods=["GET", "POST"]
)
@admin_required
def nova_categoria():

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        erro = None

        if not nome:

            erro = (
                "Informe o nome da categoria."
            )

        elif Categoria.query.filter_by(
            nome=nome
        ).first():

            erro = (
                "Já existe uma categoria com esse nome."
            )

        if erro:

            return render_template(
                "admin_categoria_form.html",
                erro=erro
            )

        db.session.add(
            Categoria(nome=nome)
        )

        db.session.commit()

        flash(
            "Categoria criada com sucesso."
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_categoria_form.html"
    )


# ============================================================
# CATEGORIAS - EDITAR
# ============================================================

@app.route(
    "/admin/categorias/<int:id>/editar",
    methods=["GET", "POST"]
)
@admin_required
def editar_categoria(id):

    categoria = Categoria.query.get_or_404(
        id
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        duplicada = Categoria.query.filter(
            Categoria.nome == nome,
            Categoria.id != categoria.id
        ).first()

        if not nome:

            return render_template(
                "admin_categoria_form.html",
                categoria=categoria,
                erro="Informe o nome da categoria."
            )

        if duplicada:

            return render_template(
                "admin_categoria_form.html",
                categoria=categoria,
                erro="Já existe uma categoria com esse nome."
            )

        categoria.nome = nome

        db.session.commit()

        flash(
            "Categoria atualizada com sucesso."
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_categoria_form.html",
        categoria=categoria
    )


# ============================================================
# CATEGORIAS - EXCLUIR
# ============================================================

@app.route(
    "/admin/categorias/<int:id>/excluir"
)
@admin_required
def excluir_categoria(id):

    categoria = Categoria.query.get_or_404(
        id
    )

    for produto in categoria.produtos:

        produto.categoria_id = None

    db.session.delete(categoria)

    db.session.commit()

    flash(
        "Categoria removida. "
        "Os produtos vinculados foram mantidos sem categoria."
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# PRODUTOS - CRIAR
# ============================================================

@app.route(
    "/admin/produtos/novo",
    methods=["GET", "POST"]
)
@admin_required
def novo_produto():

    categorias = (
        Categoria.query
        .order_by(
            Categoria.nome
        )
        .all()
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        preco_texto = request.form.get(
            "preco",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        categoria_id = (
            request.form.get(
                "categoria_id"
            )
            or None
        )

        arquivo = request.files.get(
            "imagem"
        )

        erro = None

        preco = None

        # -------------------------
        # VALIDAÇÃO
        # -------------------------

        if not nome or not preco_texto:

            erro = (
                "Preencha nome e preço do produto."
            )

        else:

            try:

                preco = float(
                    preco_texto.replace(
                        ",",
                        "."
                    )
                )

                if preco < 0:
                    raise ValueError

            except ValueError:

                erro = (
                    "Preço inválido. "
                    "Use apenas números "
                    "(ex: 59.90)."
                )

        # -------------------------
        # IMAGEM
        # -------------------------

        caminho_imagem = None

        if not erro:

            if arquivo and arquivo.filename:

                if imagem_permitida(
                    arquivo.filename
                ):

                    nome_seguro = secure_filename(
                        arquivo.filename
                    )

                    nome_final = (
                        f"{int(datetime.utcnow().timestamp())}_"
                        f"{nome_seguro}"
                    )

                    pasta_destino = (
                        app.config["UPLOAD_FOLDER"]
                    )

                    os.makedirs(
                        pasta_destino,
                        exist_ok=True
                    )

                    arquivo.save(
                        os.path.join(
                            pasta_destino,
                            nome_final
                        )
                    )

                    caminho_imagem = (
                        "assets/img/produtos/"
                        f"{nome_final}"
                    )

                else:

                    erro = (
                        "Formato de imagem não suportado. "
                        "Use JPG, PNG ou WEBP."
                    )

            else:

                erro = (
                    "Selecione uma imagem para o produto."
                )

        if erro:

            return render_template(
                "admin_produto_form.html",
                erro=erro,
                categorias=categorias
            )

        # -------------------------
        # CRIA PRODUTO
        # -------------------------

        produto = Produto(
            nome=nome,
            preco=preco,
            descricao=descricao,
            imagem=caminho_imagem,
            categoria_id=(
                int(categoria_id)
                if categoria_id
                else None
            )
        )

        db.session.add(produto)

        db.session.commit()

        flash(
            "Produto criado com sucesso."
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_produto_form.html",
        categorias=categorias
    )


# ============================================================
# PRODUTOS - EDITAR
# ============================================================

@app.route(
    "/admin/produtos/<int:id>/editar",
    methods=["GET", "POST"]
)
@admin_required
def editar_produto(id):

    produto = Produto.query.get_or_404(
        id
    )

    categorias = (
        Categoria.query
        .order_by(
            Categoria.nome
        )
        .all()
    )

    if request.method == "POST":

        nome = request.form.get(
            "nome",
            ""
        ).strip()

        preco_texto = request.form.get(
            "preco",
            ""
        ).strip()

        descricao = request.form.get(
            "descricao",
            ""
        ).strip()

        categoria_id = (
            request.form.get(
                "categoria_id"
            )
            or None
        )

        arquivo = request.files.get(
            "imagem"
        )

        erro = None

        preco = None

        # -------------------------
        # VALIDAÇÃO
        # -------------------------

        if not nome or not preco_texto:

            erro = (
                "Preencha nome e preço do produto."
            )

        else:

            try:

                preco = float(
                    preco_texto.replace(
                        ",",
                        "."
                    )
                )

                if preco < 0:
                    raise ValueError

            except ValueError:

                erro = (
                    "Preço inválido. "
                    "Use um valor maior ou igual a zero."
                )

        # -------------------------
        # IMAGEM
        # -------------------------

        caminho_imagem = produto.imagem

        if (
            not erro
            and arquivo
            and arquivo.filename
        ):

            if not imagem_permitida(
                arquivo.filename
            ):

                erro = (
                    "Formato de imagem não suportado. "
                    "Use JPG, PNG ou WEBP."
                )

            else:

                nome_seguro = secure_filename(
                    arquivo.filename
                )

                nome_final = (
                    f"{int(datetime.utcnow().timestamp())}_"
                    f"{nome_seguro}"
                )

                pasta_destino = (
                    app.config["UPLOAD_FOLDER"]
                )

                os.makedirs(
                    pasta_destino,
                    exist_ok=True
                )

                arquivo.save(
                    os.path.join(
                        pasta_destino,
                        nome_final
                    )
                )

                caminho_imagem = (
                    "assets/img/produtos/"
                    f"{nome_final}"
                )

        if erro:

            return render_template(
                "admin_produto_form.html",
                produto=produto,
                categorias=categorias,
                erro=erro
            )

        # -------------------------
        # ATUALIZA PRODUTO
        # -------------------------

        produto.nome = nome

        produto.preco = preco

        produto.descricao = descricao

        produto.categoria_id = (
            int(categoria_id)
            if categoria_id
            else None
        )

        produto.imagem = caminho_imagem

        db.session.commit()

        flash(
            "Produto atualizado com sucesso."
        )

        return redirect(
            url_for("admin_dashboard")
        )

    return render_template(
        "admin_produto_form.html",
        produto=produto,
        categorias=categorias
    )


# ============================================================
# PRODUTOS - EXCLUIR
# ============================================================

@app.route(
    "/admin/produtos/<int:id>/excluir"
)
@admin_required
def excluir_produto(id):

    produto = Produto.query.get_or_404(
        id
    )

    db.session.delete(produto)

    db.session.commit()

    flash(
        "Produto removido com sucesso."
    )

    return redirect(
        url_for("admin_dashboard")
    )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        )
    )
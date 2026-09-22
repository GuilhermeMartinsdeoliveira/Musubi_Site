from app import app, db, Produto


def test_pagina_detalhes_do_produto():
    app.config.update(TESTING=True, SQLALCHEMY_DATABASE_URI="sqlite://")

    with app.app_context():
        db.drop_all()
        db.create_all()
        produto = Produto(
            nome="Vaso Decorativo",
            preco=79.9,
            descricao="Vaso artesanal para decoração.",
            imagem="assets/img/produtos/vaso.jpg",
        )
        db.session.add(produto)
        db.session.commit()

        client = app.test_client()
        response = client.get(f"/produto/{produto.id}")

        assert response.status_code == 200
        assert b"Vaso Decorativo" in response.data
        assert b"Detalhes do produto" in response.data

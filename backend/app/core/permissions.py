ALL_PERMISSIONS: tuple[str, ...] = (
    "cliente.ler",
    "cliente.criar",
    "cliente.atualizar",
    "cliente.excluir",
    "produto.ler",
    "produto.criar",
    "produto.atualizar",
    "produto.excluir",
    "categoria.ler",
    "categoria.criar",
    "categoria.atualizar",
    "categoria.excluir",
    "pedido.ler",
    "pedido.criar",
    "pedido.atualizar",
    "pedido.cancelar",
    "estoque.ler",
    "estoque.atualizar",
    "user.ler",
    "user.criar",
    "user.atualizar",
    "user.excluir",
    "role.ler",
    "role.criar",
    "role.atualizar",
    "role.excluir",
    "permission.ler",
)

MANAGER_EXCLUDED: frozenset[str] = frozenset(
    {
        "user.excluir",
        "role.excluir",
        "permission.ler",
    }
)

READ_PERMISSIONS: frozenset[str] = frozenset(
    {
        "cliente.ler",
        "produto.ler",
        "categoria.ler",
        "pedido.ler",
        "estoque.ler",
        "user.ler",
        "role.ler",
        "permission.ler",
    }
)

LEGACY_RENAMES: dict[str, str] = {
    "user.read": "user.ler",
    "user.create": "user.criar",
    "user.update": "user.atualizar",
    "user.delete": "user.excluir",
    "role.read": "role.ler",
    "role.create": "role.criar",
    "role.update": "role.atualizar",
    "role.delete": "role.excluir",
    "permission.read": "permission.ler",
}

PROFILES: tuple[tuple[str, str], ...] = (
    ("admin", "Administrador do sistema"),
    ("manager", "Gerente"),
    ("viewer", "Visualizador"),
)

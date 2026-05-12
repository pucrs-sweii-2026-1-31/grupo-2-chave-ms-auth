class AuthenticationError(Exception):
    """Exceção para erros de autenticação (401)."""
    pass


class ConflictError(Exception):
    """Exceção para conflitos de recurso, como usuário já existente (409)."""
    pass

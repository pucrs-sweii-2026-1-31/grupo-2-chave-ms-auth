import pytest
from unittest.mock import MagicMock, patch
import jwt
import datetime
import bcrypt
from auth_service.services.auth_service import AuthService
from auth_service.services.exceptions import AuthenticationError, ConflictError

@pytest.fixture
def mock_repo():
    return MagicMock()

@pytest.fixture
def auth_service(mock_repo):
    with patch('auth_service.services.auth_service.Config') as mock_config:
        mock_config.JWT_SECRET = 'test_secret'
        service = AuthService(mock_repo)
        service.access_expires = 900
        service.refresh_expires = 86400
        return service

def test_login_success(auth_service, mock_repo):
    # Setup
    email = "test@example.com"
    password = "password123"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    mock_user = MagicMock()
    mock_user.id = 1
    mock_user.password_hash = password_hash
    mock_repo.get_by_email.return_value = mock_user
    
    # Execute
    access_token, refresh_token = auth_service.login({"email": email, "password": password})
    
    # Verify
    assert access_token is not None
    assert refresh_token is not None
    mock_repo.get_by_email.assert_called_once_with(email)
    mock_repo.commit.assert_called_once()
    assert mock_user.refresh_token == refresh_token

def test_login_invalid_credentials(auth_service, mock_repo):
    # Setup
    email = "test@example.com"
    password = "wrongpassword"
    mock_repo.get_by_email.return_value = None
    
    # Execute & Verify
    with pytest.raises(AuthenticationError, match="Credenciais inválidas."):
        auth_service.login({"email": email, "password": password})

def test_refresh_token_success(auth_service, mock_repo):
    # Setup
    user_id = "1"
    refresh_token = auth_service._create_token({"sub": user_id, "type": "refresh"}, 86400)
    
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.refresh_token = refresh_token
    mock_repo.get_by_id.return_value = mock_user
    
    # Execute
    new_access_token = auth_service.refresh({"refresh_token": refresh_token})
    
    # Verify
    assert new_access_token is not None
    payload = jwt.decode(new_access_token, auth_service.secret_key, algorithms=["HS256"])
    assert payload["sub"] == user_id
    assert payload["type"] == "access"

def test_refresh_token_invalid_type(auth_service, mock_repo):
    # Setup
    user_id = "1"
    invalid_token = auth_service._create_token({"sub": user_id, "type": "access"}, 900)
    
    # Execute & Verify
    with pytest.raises(AuthenticationError, match="Token de refresh inválido."):
        auth_service.refresh({"refresh_token": invalid_token})

def test_refresh_token_mismatch(auth_service, mock_repo):
    # Setup
    user_id = "1"
    refresh_token = auth_service._create_token({"sub": user_id, "type": "refresh"}, 86400)
    
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.refresh_token = "different_token"
    mock_repo.get_by_id.return_value = mock_user
    
    # Execute & Verify
    with pytest.raises(AuthenticationError, match="Token de refresh inválido."):
        auth_service.refresh({"refresh_token": refresh_token})

def test_register_user_success(auth_service, mock_repo):
    # Setup
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    mock_repo.get_by_username_or_email.return_value = None
    
    mock_new_user = MagicMock()
    mock_new_user.id = 1
    mock_new_user.to_dict.return_value = {"id": 1, "username": "testuser", "email": "test@example.com"}
    mock_repo.create.return_value = mock_new_user
    
    # Mock login success inside register
    password_hash = bcrypt.hashpw(data["password"].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    mock_new_user.password_hash = password_hash
    mock_repo.get_by_email.return_value = mock_new_user
    
    # Execute
    result = auth_service.register(data)
    
    # Verify
    assert result["message"] == "Usuário registrado com sucesso."
    assert "access_token" in result
    assert "refresh_token" in result
    assert result["user"]["username"] == "testuser"
    mock_repo.create.assert_called_once()
    assert mock_repo.commit.call_count >= 1

def test_register_user_already_exists(auth_service, mock_repo):
    # Setup
    data = {
        "username": "existinguser",
        "email": "existing@example.com",
        "password": "password123"
    }
    mock_repo.get_by_username_or_email.return_value = MagicMock()
    
    # Execute & Verify
    with pytest.raises(ConflictError, match="Username ou email já cadastrado."):
        auth_service.register(data)

def test_register_validation_error(auth_service):
    # Setup
    data = {
        "username": "user",
        "email": "email@example.com",
        "password": "123" # too short
    }
    
    # Execute & Verify
    with pytest.raises(ValueError, match="Senha deve ter pelo menos 6 caracteres."):
        auth_service.register(data)

def test_update_user_role_success(auth_service, mock_repo):
    # Setup
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = {"id": 2, "roles": ["admin"]}
    target_user = MagicMock()
    target_user.id = 1
    target_user.roles = ["user"]
    target_user.to_dict.return_value = {"id": 1, "roles": ["user", "admin"]}
    
    # Mock get_current_user logic (get_by_id for admin check)
    def side_effect(user_id):
        if str(user_id) == "2":
            m = MagicMock()
            m.to_dict.return_value = admin_user
            return m
        if str(user_id) == "1":
            return target_user
        return None
        
    mock_repo.get_by_id.side_effect = side_effect
    
    # Execute
    result = auth_service.update_user_role(1, {"role": "admin"}, auth_header)
    
    # Verify
    assert result["message"] == "Role do usuário atualizado com sucesso."
    assert "admin" in target_user.roles
    mock_repo.commit.assert_called()

def test_update_user_role_invalid_role(auth_service, mock_repo):
    # Setup
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = {"id": 2, "roles": ["admin"]}
    mock_repo.get_by_id.return_value.to_dict.return_value = admin_user
    
    # Execute & Verify
    with pytest.raises(ValueError, match="Role inválido."):
        auth_service.update_user_role(1, {"role": "super-admin"}, auth_header)

def test_update_user_role_unauthorized(auth_service, mock_repo):
    # Setup
    user_token = auth_service._create_token({"sub": "3", "type": "access"}, 900)
    auth_header = f"Bearer {user_token}"
    
    regular_user = {"id": 3, "roles": ["user"]}
    mock_repo.get_by_id.return_value.to_dict.return_value = regular_user
    
    # Execute & Verify
    with pytest.raises(PermissionError, match="Acesso negado."):
        auth_service.update_user_role(1, {"role": "admin"}, auth_header)

def test_logout_success(auth_service, mock_repo):
    # Setup
    user_id = "1"
    refresh_token = auth_service._create_token({"sub": user_id, "type": "refresh"}, 86400)
    
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_repo.get_by_id.return_value = mock_user
    
    # Execute
    auth_service.logout({"refresh_token": refresh_token})
    
    # Verify
    assert mock_user.refresh_token is None
    mock_repo.commit.assert_called_once()

def test_get_current_user_success(auth_service, mock_repo):
    # Setup
    user_id = "1"
    access_token = auth_service._create_token({"sub": user_id, "type": "access"}, 900)
    auth_header = f"Bearer {access_token}"
    
    mock_user = MagicMock()
    mock_user.to_dict.return_value = {"id": user_id, "username": "testuser"}
    mock_repo.get_by_id.return_value = mock_user
    
    # Execute
    user_data = auth_service.get_current_user(auth_header)
    
    # Verify
    assert user_data["id"] == user_id
    mock_repo.get_by_id.assert_called_with(user_id)

def test_get_all_users_success(auth_service, mock_repo):
    # Setup
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = MagicMock()
    admin_user.to_dict.return_value = {"id": 2, "roles": ["admin"]}
    
    user1 = MagicMock()
    user1.to_dict.return_value = {"id": 1, "username": "user1"}
    
    def side_effect(user_id):
        if str(user_id) == "2": return admin_user
        return None
    mock_repo.get_by_id.side_effect = side_effect
    
    mock_repo.list_all.return_value = [user1]
    mock_repo.count_all.return_value = 1
    
    # Execute
    result = auth_service.get_all_users(auth_header)
    
    # Verify
    assert len(result["users"]) == 1
    assert result["total"] == 1
    assert result["users"][0]["username"] == "user1"

def test_get_user_by_id_success(auth_service, mock_repo):
    # Setup
    user_id = "1"
    access_token = auth_service._create_token({"sub": user_id, "type": "access"}, 900)
    auth_header = f"Bearer {access_token}"
    
    mock_user = MagicMock()
    mock_user.id = user_id
    mock_user.to_dict.return_value = {"id": user_id, "username": "testuser"}
    mock_repo.get_by_id.return_value = mock_user
    
    # Execute
    user_data = auth_service.get_user_by_id(user_id, auth_header)
    
    # Verify
    assert user_data["id"] == user_id

def test_update_user_status_success(auth_service, mock_repo):
    # Setup
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = {"id": 2, "roles": ["admin"]}
    target_user = MagicMock()
    target_user.id = 1
    target_user.status = "active"
    target_user.to_dict.return_value = {"id": 1, "status": "banned"}
    
    def side_effect(user_id):
        if str(user_id) == "2":
            m = MagicMock()
            m.to_dict.return_value = admin_user
            return m
        if str(user_id) == "1":
            return target_user
        return None
    mock_repo.get_by_id.side_effect = side_effect
    
    # Execute
    result = auth_service.update_user_status(1, {"status": "banned"}, auth_header)
    
    # Verify
    assert result["message"] == "Status do usuário atualizado com sucesso."
    assert target_user.status == "banned"
    mock_repo.commit.assert_called()

def test_login_missing_fields(auth_service):
    with pytest.raises(ValueError, match="Email e senha são obrigatórios."):
        auth_service.login({"email": "test@example.com"})
    with pytest.raises(ValueError, match="Email e senha são obrigatórios."):
        auth_service.login({"password": "password123"})

def test_refresh_missing_token(auth_service):
    with pytest.raises(ValueError, match="Refresh token é obrigatório."):
        auth_service.refresh({})

def test_logout_missing_token(auth_service):
    with pytest.raises(ValueError, match="Refresh token é obrigatório."):
        auth_service.logout({})

def test_register_missing_fields(auth_service):
    with pytest.raises(ValueError, match="Username, email e senha são obrigatórios."):
        auth_service.register({"email": "test@example.com", "password": "password123"})
    with pytest.raises(ValueError, match="Username, email e senha são obrigatórios."):
        auth_service.register({"username": "testuser", "password": "password123"})
    with pytest.raises(ValueError, match="Username, email e senha são obrigatórios."):
        auth_service.register({"username": "testuser", "email": "test@example.com"})

def test_update_user_role_missing_field(auth_service, mock_repo):
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    admin_user = MagicMock()
    admin_user.to_dict.return_value = {"id": 2, "roles": ["admin"]}
    mock_repo.get_by_id.return_value = admin_user
    
    with pytest.raises(ValueError, match="Campo 'role' é obrigatório."):
        auth_service.update_user_role(1, {}, auth_header)

def test_update_user_status_missing_field(auth_service, mock_repo):
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    admin_user = MagicMock()
    admin_user.to_dict.return_value = {"id": 2, "roles": ["admin"]}
    mock_repo.get_by_id.return_value = admin_user
    
    with pytest.raises(ValueError, match="Campo 'status' é obrigatório."):
        auth_service.update_user_status(1, {}, auth_header)

def test_get_all_users_unauthorized(auth_service, mock_repo):
    user_token = auth_service._create_token({"sub": "3", "type": "access"}, 900)
    auth_header = f"Bearer {user_token}"
    regular_user = MagicMock()
    regular_user.to_dict.return_value = {"id": 3, "roles": ["user"]}
    mock_repo.get_by_id.return_value = regular_user
    
    with pytest.raises(PermissionError, match="Acesso negado."):
        auth_service.get_all_users(auth_header)

def test_get_user_by_id_unauthorized(auth_service, mock_repo):
    user_token = auth_service._create_token({"sub": "3", "type": "access"}, 900)
    auth_header = f"Bearer {user_token}"
    regular_user = MagicMock()
    regular_user.to_dict.return_value = {"id": 3, "roles": ["user"]}
    
    def side_effect(user_id):
        if str(user_id) == "3": return regular_user
        return None
    mock_repo.get_by_id.side_effect = side_effect
    
    with pytest.raises(PermissionError, match="Acesso negado."):
        auth_service.get_user_by_id(1, auth_header)

def test_update_user_status_unauthorized(auth_service, mock_repo):
    user_token = auth_service._create_token({"sub": "3", "type": "access"}, 900)
    auth_header = f"Bearer {user_token}"
    regular_user = MagicMock()
    regular_user.to_dict.return_value = {"id": 3, "roles": ["user"]}
    mock_repo.get_by_id.return_value = regular_user
    
    with pytest.raises(PermissionError, match="Acesso negado."):
        auth_service.update_user_status(1, {"status": "banned"}, auth_header)

def test_get_current_user_not_found(auth_service, mock_repo):
    access_token = auth_service._create_token({"sub": "999", "type": "access"}, 900)
    auth_header = f"Bearer {access_token}"
    mock_repo.get_by_id.return_value = None
    
    with pytest.raises(AuthenticationError, match="Usuário não encontrado."):
        auth_service.get_current_user(auth_header)

def test_get_user_by_id_not_found(auth_service, mock_repo):
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = MagicMock()
    admin_user.to_dict.return_value = {"id": 2, "roles": ["admin"]}
    
    def side_effect(user_id):
        if str(user_id) == "2": return admin_user
        return None
    mock_repo.get_by_id.side_effect = side_effect
    
    with pytest.raises(LookupError, match="Usuário não encontrado."):
        auth_service.get_user_by_id(999, auth_header)

def test_db_commit_failure_during_login(auth_service, mock_repo):
    email = "test@example.com"
    password = "password123"
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    mock_user = MagicMock()
    mock_user.password_hash = password_hash
    mock_repo.get_by_email.return_value = mock_user
    mock_repo.commit.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        auth_service.login({"email": email, "password": password})

def test_db_commit_failure_during_register(auth_service, mock_repo):
    data = {"username": "u", "email": "e", "password": "password"}
    mock_repo.get_by_username_or_email.return_value = None
    mock_repo.commit.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        auth_service.register(data)

def test_db_commit_failure_during_logout(auth_service, mock_repo):
    user_id = "1"
    refresh_token = auth_service._create_token({"sub": user_id, "type": "refresh"}, 86400)
    mock_repo.get_by_id.return_value = MagicMock()
    mock_repo.commit.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        auth_service.logout({"refresh_token": refresh_token})

def test_db_commit_failure_during_role_update(auth_service, mock_repo):
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = MagicMock()
    admin_user.to_dict.return_value = {"id": 2, "roles": ["admin"]}
    target_user = MagicMock()
    target_user.roles = ["user"]
    
    def side_effect(user_id):
        if str(user_id) == "2": return admin_user
        return target_user
    mock_repo.get_by_id.side_effect = side_effect
    mock_repo.commit.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        auth_service.update_user_role(1, {"role": "admin"}, auth_header)

def test_db_commit_failure_during_status_update(auth_service, mock_repo):
    admin_token = auth_service._create_token({"sub": "2", "type": "access"}, 900)
    auth_header = f"Bearer {admin_token}"
    
    admin_user = MagicMock()
    admin_user.to_dict.return_value = {"id": 2, "roles": ["admin"]}
    target_user = MagicMock()
    
    def side_effect(user_id):
        if str(user_id) == "2": return admin_user
        return target_user
    mock_repo.get_by_id.side_effect = side_effect
    mock_repo.commit.side_effect = Exception("DB Error")
    
    with pytest.raises(Exception, match="DB Error"):
        auth_service.update_user_status(1, {"status": "banned"}, auth_header)

def test_decode_token_expired(auth_service):
    # Create an already expired token by passing a negative expiration
    expired_token = auth_service._create_token({"sub": "1"}, -10)
    
    with pytest.raises(AuthenticationError, match="Token expirado."):
        auth_service._decode_token(expired_token)

def test_decode_token_invalid(auth_service):
    with pytest.raises(AuthenticationError, match="Token inválido"):
        auth_service._decode_token("invalid.token.here")

def test_get_current_user_invalid_header(auth_service):
    with pytest.raises(AuthenticationError, match="Authorization header inválido."):
        auth_service.get_current_user("NotBearer token")
    with pytest.raises(AuthenticationError, match="Authorization header inválido."):
        auth_service.get_current_user("")

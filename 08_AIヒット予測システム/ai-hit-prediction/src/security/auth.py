#!/usr/bin/env python
"""
Security and Authentication Module
セキュリティとAPI認証システム
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
import json

# セキュリティライブラリ
from passlib.context import CryptContext
from jose import JWTError, jwt

# Rate limiting
try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    SLOWAPI_AVAILABLE = True
except ImportError:
    SLOWAPI_AVAILABLE = False

# 暗号化
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class SecurityConfig:
    """セキュリティ設定"""
    
    # JWT設定
    SECRET_KEY = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    
    # パスワード設定
    MIN_PASSWORD_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGITS = True
    REQUIRE_SPECIAL = True
    
    # API設定
    API_KEY_LENGTH = 32
    API_KEY_PREFIX = "ahp_"  # AI Hit Prediction
    
    # Rate limiting
    DEFAULT_RATE_LIMIT = "100/hour"
    BURST_RATE_LIMIT = "10/minute"


class PasswordManager:
    """パスワード管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.pwd_context = CryptContext(
            schemes=["argon2", "bcrypt"],
            deprecated="auto",
            argon2__rounds=4,
            argon2__memory_cost=65536,
            argon2__parallelism=2
        )
    
    def hash_password(self, password: str) -> str:
        """
        パスワードのハッシュ化
        
        Args:
            password: プレーンテキストパスワード
        
        Returns:
            ハッシュ化されたパスワード
        """
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        パスワード検証
        
        Args:
            plain_password: プレーンテキストパスワード
            hashed_password: ハッシュ化されたパスワード
        
        Returns:
            検証結果
        """
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """
        パスワード強度検証
        
        Args:
            password: 検証するパスワード
        
        Returns:
            検証結果
        """
        errors = []
        
        if len(password) < SecurityConfig.MIN_PASSWORD_LENGTH:
            errors.append(f"Password must be at least {SecurityConfig.MIN_PASSWORD_LENGTH} characters")
        
        if SecurityConfig.REQUIRE_UPPERCASE and not any(c.isupper() for c in password):
            errors.append("Password must contain uppercase letters")
        
        if SecurityConfig.REQUIRE_LOWERCASE and not any(c.islower() for c in password):
            errors.append("Password must contain lowercase letters")
        
        if SecurityConfig.REQUIRE_DIGITS and not any(c.isdigit() for c in password):
            errors.append("Password must contain digits")
        
        if SecurityConfig.REQUIRE_SPECIAL:
            special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
            if not any(c in special_chars for c in password):
                errors.append("Password must contain special characters")
        
        # エントロピー計算
        entropy = self._calculate_entropy(password)
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'entropy': entropy,
            'strength': self._get_strength_level(entropy)
        }
    
    def _calculate_entropy(self, password: str) -> float:
        """パスワードのエントロピー計算"""
        charset_size = 0
        
        if any(c.islower() for c in password):
            charset_size += 26
        if any(c.isupper() for c in password):
            charset_size += 26
        if any(c.isdigit() for c in password):
            charset_size += 10
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            charset_size += 32
        
        if charset_size == 0:
            return 0
        
        import math
        return len(password) * math.log2(charset_size)
    
    def _get_strength_level(self, entropy: float) -> str:
        """強度レベル判定"""
        if entropy < 30:
            return "weak"
        elif entropy < 50:
            return "fair"
        elif entropy < 70:
            return "good"
        elif entropy < 90:
            return "strong"
        else:
            return "very_strong"


class TokenManager:
    """トークン管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.secret_key = SecurityConfig.SECRET_KEY
        self.algorithm = SecurityConfig.ALGORITHM
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        アクセストークン作成
        
        Args:
            data: トークンに含めるデータ
            expires_delta: 有効期限
        
        Returns:
            JWTトークン
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=SecurityConfig.ACCESS_TOKEN_EXPIRE_MINUTES
            )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """
        リフレッシュトークン作成
        
        Args:
            data: トークンに含めるデータ
        
        Returns:
            リフレッシュトークン
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=SecurityConfig.REFRESH_TOKEN_EXPIRE_DAYS
        )
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Optional[Dict]:
        """
        トークン検証
        
        Args:
            token: 検証するトークン
            token_type: トークンタイプ
        
        Returns:
            デコードされたペイロード
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != token_type:
                return None
            
            return payload
            
        except JWTError:
            return None
    
    def revoke_token(self, token: str):
        """トークン無効化（ブラックリスト管理が必要）"""
        # Redis等でブラックリスト管理を実装
        pass


class APIKeyManager:
    """APIキー管理クラス"""
    
    def __init__(self):
        """初期化"""
        self.keys_storage = {}  # 本番環境ではデータベース使用
    
    def generate_api_key(self, user_id: str, name: str, 
                        permissions: List[str]) -> Dict[str, Any]:
        """
        APIキー生成
        
        Args:
            user_id: ユーザーID
            name: キーの名前
            permissions: 権限リスト
        
        Returns:
            APIキー情報
        """
        # ランダムキー生成
        raw_key = secrets.token_urlsafe(SecurityConfig.API_KEY_LENGTH)
        api_key = f"{SecurityConfig.API_KEY_PREFIX}{raw_key}"
        
        # キーハッシュ（保存用）
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # メタデータ
        key_data = {
            'id': secrets.token_urlsafe(16),
            'user_id': user_id,
            'name': name,
            'key_hash': key_hash,
            'permissions': permissions,
            'created_at': datetime.utcnow().isoformat(),
            'last_used': None,
            'is_active': True
        }
        
        # 保存
        self.keys_storage[key_hash] = key_data
        
        return {
            'api_key': api_key,  # 初回のみ返す
            'key_id': key_data['id'],
            'name': name,
            'created_at': key_data['created_at']
        }
    
    def verify_api_key(self, api_key: str) -> Optional[Dict]:
        """
        APIキー検証
        
        Args:
            api_key: 検証するAPIキー
        
        Returns:
            キー情報
        """
        if not api_key.startswith(SecurityConfig.API_KEY_PREFIX):
            return None
        
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_data = self.keys_storage.get(key_hash)
        
        if key_data and key_data['is_active']:
            # 最終使用時刻更新
            key_data['last_used'] = datetime.utcnow().isoformat()
            return key_data
        
        return None
    
    def revoke_api_key(self, key_id: str) -> bool:
        """
        APIキー無効化
        
        Args:
            key_id: キーID
        
        Returns:
            成功フラグ
        """
        for key_hash, key_data in self.keys_storage.items():
            if key_data['id'] == key_id:
                key_data['is_active'] = False
                key_data['revoked_at'] = datetime.utcnow().isoformat()
                return True
        
        return False


class DataEncryption:
    """データ暗号化クラス"""
    
    def __init__(self, password: Optional[str] = None):
        """
        初期化
        
        Args:
            password: 暗号化パスワード
        """
        if password:
            self.key = self._derive_key(password)
        else:
            self.key = Fernet.generate_key()
        
        self.cipher = Fernet(self.key)
    
    def _derive_key(self, password: str) -> bytes:
        """パスワードから暗号化キー導出"""
        password_bytes = password.encode()
        salt = b'ai-hit-prediction-salt'  # 本番環境では安全な乱数を使用
        
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return key
    
    def encrypt_data(self, data: Any) -> str:
        """
        データ暗号化
        
        Args:
            data: 暗号化するデータ
        
        Returns:
            暗号化されたデータ（Base64）
        """
        # JSONシリアライズ
        json_data = json.dumps(data, ensure_ascii=False)
        
        # 暗号化
        encrypted = self.cipher.encrypt(json_data.encode())
        
        return encrypted.decode()
    
    def decrypt_data(self, encrypted_data: str) -> Any:
        """
        データ復号化
        
        Args:
            encrypted_data: 暗号化されたデータ
        
        Returns:
            復号化されたデータ
        """
        # 復号化
        decrypted = self.cipher.decrypt(encrypted_data.encode())
        
        # JSONデシリアライズ
        return json.loads(decrypted.decode())


class RateLimiter:
    """レート制限クラス"""
    
    def __init__(self):
        """初期化"""
        if SLOWAPI_AVAILABLE:
            self.limiter = Limiter(
                key_func=get_remote_address,
                default_limits=[SecurityConfig.DEFAULT_RATE_LIMIT]
            )
        else:
            self.limiter = None
    
    def get_limiter(self):
        """リミッター取得"""
        return self.limiter
    
    def create_custom_limit(self, rate: str):
        """カスタムレート制限作成"""
        if self.limiter:
            return self.limiter.limit(rate)
        return lambda f: f  # No-op decorator


class SecurityValidator:
    """セキュリティ検証クラス"""
    
    @staticmethod
    def validate_input(data: str, max_length: int = 1000) -> bool:
        """
        入力データ検証
        
        Args:
            data: 検証するデータ
            max_length: 最大長
        
        Returns:
            検証結果
        """
        # 長さチェック
        if len(data) > max_length:
            return False
        
        # SQLインジェクション対策
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', 'EXEC']
        data_upper = data.upper()
        for keyword in sql_keywords:
            if keyword in data_upper:
                return False
        
        # XSS対策
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        data_lower = data.lower()
        for pattern in xss_patterns:
            if pattern in data_lower:
                return False
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        ファイル名のサニタイズ
        
        Args:
            filename: サニタイズするファイル名
        
        Returns:
            安全なファイル名
        """
        # 危険な文字を削除
        import re
        sanitized = re.sub(r'[^\w\s.-]', '', filename)
        sanitized = re.sub(r'\.+', '.', sanitized)
        
        # パストラバーサル対策
        sanitized = sanitized.replace('..', '')
        sanitized = sanitized.replace('/', '')
        sanitized = sanitized.replace('\\', '')
        
        return sanitized[:255]  # 最大長制限
    
    @staticmethod
    def validate_url(url: str) -> bool:
        """
        URL検証
        
        Args:
            url: 検証するURL
        
        Returns:
            検証結果
        """
        from urllib.parse import urlparse
        
        try:
            result = urlparse(url)
            
            # スキーム確認
            if result.scheme not in ['http', 'https']:
                return False
            
            # ホスト確認
            if not result.netloc:
                return False
            
            # プライベートIP確認
            import ipaddress
            try:
                ip = ipaddress.ip_address(result.hostname)
                if ip.is_private or ip.is_loopback:
                    return False
            except:
                pass  # ドメイン名の場合
            
            return True
            
        except:
            return False


# セキュリティミドルウェア
class SecurityMiddleware:
    """セキュリティミドルウェア"""
    
    def __init__(self):
        """初期化"""
        self.password_manager = PasswordManager()
        self.token_manager = TokenManager()
        self.api_key_manager = APIKeyManager()
        self.rate_limiter = RateLimiter()
        self.validator = SecurityValidator()
    
    def add_security_headers(self, response):
        """セキュリティヘッダー追加"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'"
        return response


# グローバルインスタンス
security_middleware = SecurityMiddleware()
password_manager = PasswordManager()
token_manager = TokenManager()
api_key_manager = APIKeyManager()
data_encryption = DataEncryption()
rate_limiter = RateLimiter()
security_validator = SecurityValidator()


import base64
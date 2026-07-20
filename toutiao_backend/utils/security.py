from passlib.context import CryptContext

# 创建密码上下文
# schemes=["bcrypt"] 加密算法
# deprecated="auto"  新旧加密算法自适应
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# 密码加密
def get_hash_password(password: str):
    return pwd_context.hash(password)


# 密码验证：verify 返回值是布尔型
def verify_password(plain_password, hashed_password):
    """
    验证密码是否正确

    :param plain_password:明文密码（用户输入的）
    :param hashed_password:哈希密码（数据库存储的）
    :return:True-密码正确，False-密码错误
    """
    return pwd_context.verify(plain_password, hashed_password)

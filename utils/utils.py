from passlib.hash import pbkdf2_sha256 # 암호화, 일반적으로 사용 sha256

# 원문 비밀번호를 암호화 하는 함수
# hash : 암호화 하는 함수
def hash_password(original_password) :
    salt = 'yh*hello12'
    password = original_password + salt
    password = pbkdf2_sha256.hash(password)
    return password

def onlyalphanum(check):
    for c in check:
        val = ord(c)
        if 65 <= val <= 90:
            continue
        elif 97 <= val <= 122:
            continue
        elif c.isdigit():
            continue
        else:
            return False
    return True

def verfifyPwd(inputPwd, hashed_password):
    salt = 'yh*hello12'
    return pbkdf2_sha256.verify(inputPwd+salt, hashed_password)
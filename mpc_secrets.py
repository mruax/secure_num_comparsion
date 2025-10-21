class SecretShare:
    """Класс для арифметического разделения секретов по модулю"""
    
    def __init__(self, share: int, modulus: int = 2**32):
        self.share = share % modulus
        self.modulus = modulus
    
    def __add__(self, other):
        if isinstance(other, SecretShare):
            return SecretShare((self.share + other.share) % self.modulus, self.modulus)
        return SecretShare((self.share + other) % self.modulus, self.modulus)
    
    def __sub__(self, other):
        if isinstance(other, SecretShare):
            return SecretShare((self.share - other.share) % self.modulus, self.modulus)
        return SecretShare((self.share - other) % self.modulus, self.modulus)
    
    def __mul__(self, scalar: int):
        """Умножение на публичную константу"""
        return SecretShare((self.share * scalar) % self.modulus, self.modulus)


class BinaryShare:
    """Класс для двоичного разделения секретов (XOR-based)"""
    
    def __init__(self, share: int):
        self.share = share
    
    def __xor__(self, other):
        if isinstance(other, BinaryShare):
            return BinaryShare(self.share ^ other.share)
        return BinaryShare(self.share ^ other)

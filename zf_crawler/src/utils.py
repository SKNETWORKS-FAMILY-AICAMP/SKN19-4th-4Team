KO_PARTICLES = ['을', '를', '이', '가', '은', '는', '의', '에', '로', '으로', '에서', '과', '와']


def strip_particles(word: str) -> str:
    """한국어 조사 제거"""
    for suffix in KO_PARTICLES:
        if word.endswith(suffix) and len(word) > len(suffix):
            return word[:-len(suffix)]
    return word
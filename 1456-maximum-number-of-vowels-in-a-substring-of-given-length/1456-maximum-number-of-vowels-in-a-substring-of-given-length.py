class Solution:
    def maxVowels(self, s: str, k: int) -> int:
        count = 0
        vow = set("AEIOUaeiou")
        for i in range(k):
            if s[i] in vow:
                count += 1
        m = count
        for i in range(k,len(s)):
            if s[i-k] in vow:
                count -= 1
            if s[i] in vow:
                count += 1
            m = max(m,count)
        return m
class Solution:
    def firstPalindrome(self, words: List[str]) -> str:
        def ispali(s):
            st,end = 0,len(s) - 1
            while st < end:
                if s[st] != s[end]:
                    return False
                st += 1
                end -= 1
            return True
        for s in words:
            if ispali(s):
                return s
        return ""
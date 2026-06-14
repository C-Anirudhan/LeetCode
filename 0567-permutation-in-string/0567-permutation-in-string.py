class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        if len(s1) > len(s2):
            return False
        sc = [0] * 26
        wc =[0] * 26
        k = len(s1)
        for i in range(k):
            sc[ord(s1[i]) - ord('a')] += 1
            wc[ord(s2[i]) - ord('a')] += 1
        if sc == wc:
            return True
        for i in range(k,len(s2)):
            wc[ord(s2[i-k]) - ord('a')] -= 1
            wc[ord(s2[i]) - ord('a')] += 1 
            
            if wc == sc:
                return True
        return False
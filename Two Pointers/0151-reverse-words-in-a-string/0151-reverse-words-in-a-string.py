class Solution:
    def reverseWords(self, s: str) -> str:
        s = s.split()
        st,end = 0,len(s)-1
        while st < end:
            s[st],s[end] = s[end],s[st]
            st += 1
            end -= 1
        return " ".join(s)
class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> bool:
        n = len(s)
        dp = [False] * (n + 1)
        dp[0] = True
        for i in range(n):
            if dp[i]:
                for w in wordDict:
                    l = len(w)
                    if i +l <= n and s[i:i+l] == w:
                        dp[i+l] = True
        return dp[n]
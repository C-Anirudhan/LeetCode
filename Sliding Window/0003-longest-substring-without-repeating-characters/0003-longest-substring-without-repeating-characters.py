class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        n = len(s)
        map = {}
        start = 0
        ans = 0
        for end in range(n):
            curr = s[end]
            if curr in map:
                start = max(start,map[curr] + 1)
            map[curr] = end
            ans = max(ans,(end - start + 1))
        return ans
                 
            
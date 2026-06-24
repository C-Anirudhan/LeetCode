class Solution:
    def shortestToChar(self, s: str, c: str) -> List[int]:
        n = len(s)
        ans = [-1]* n

        start,end = 0,0
        prev = -1
        while end < n and start <= end:
            while end < n and s[end] != c:
                if prev != -1:
                    ans[end] = end - prev
                end += 1
            if end < n:
                while start <= end:
                    if prev != -1 and (start - prev) < (end - start):
                        ans[start] = (start - prev)
                    else:
                        ans[start] = (end - start)
                    start += 1
                prev = end
                start = end + 1
                end += 1
                continue
            start += 1
            end += 1
        return ans


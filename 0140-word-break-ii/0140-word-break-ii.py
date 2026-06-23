class Solution:
    def wordBreak(self, s: str, wordDict: List[str]) -> List[str]:
        def solve(target,arr,memo = None):
            if memo is None:
                memo = {}
            if target in memo:
                return memo[target]
            if target == "":
                return [""]

            ans = []
            for i in arr:
                if target.startswith(i):
                    res = solve(target[len(i):],arr,memo)
                    for tail in res:
                        if tail == "":
                            ans.append(i)
                        else:
                            ans.append(i + ' ' + tail)
            memo[target] = ans
            return memo[target] 
        return (solve(s,wordDict))
    

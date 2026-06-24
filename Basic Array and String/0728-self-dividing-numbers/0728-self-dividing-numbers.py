class Solution:
    def selfDividingNumbers(self, left: int, right: int) -> List[int]:
        ans = []
        for i in range(left,right + 1):
            dup = i
            valid = True
            while dup != 0:
                d = dup % 10
                if d == 0 or i % d != 0:
                    valid = False
                    break
                dup = dup // 10
            if valid:
                ans.append(i)
        return ans
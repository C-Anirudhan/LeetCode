class Solution:
    def climbStairs(self, n: int) -> int:
        if n <= 2:
            return n
        f,s = 1,2
        num = 1
        for i in range(2,n):
            num = f + s
            f = s
            s = num
        return num

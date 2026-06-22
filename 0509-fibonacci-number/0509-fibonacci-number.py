class Solution:
    def fib(self, n: int) -> int:
        if n <= 1:
            return n
        f,s = 0,1
        num = 1
        for i in range(1,n):
            num = f + s
            f = s
            s = num
        return num 
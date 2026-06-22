class Solution:
    def trailingZeroes(self, n: int) -> int:
        curr = 5
        count = 0
        while n >= curr:
            count += (n//curr)
            curr *= 5
        return count
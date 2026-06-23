class Solution:
    def getRow(self, rowIndex: int) -> List[int]:
        prev= [1]
        for i in range(1,rowIndex+1):
            dp = [1]*(i+1)
            for j in range(1,i):
                dp[j] = prev[j] + prev[j-1]
            prev = dp
        return prev
        
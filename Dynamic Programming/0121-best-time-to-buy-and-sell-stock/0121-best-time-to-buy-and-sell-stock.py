class Solution:
    def maxProfit(self, prices: List[int]) -> int:
        mp = 0
        min_price = prices[0]
        for i in range(1,len(prices)):
            if prices[i] < min_price:
                min_price = prices[i]
                continue
            mp = max(mp,prices[i] - min_price)
        return mp
class Solution:
    def maximumSubarraySum(self, nums: List[int], k: int) -> int:
        if len(nums) < k:
            return 0
        hash = {}
        s = 0
        corr = True
        for i in range(k):
            if nums[i] in hash:
                corr = False
            s += nums[i]
            hash[nums[i]] = hash.get(nums[i],0) + 1
        m = 0
        if corr:
            m = s
        for i in range(k,len(nums)):
            s -= nums[i-k]
            hash[nums[i-k]] -= 1
            if hash[nums[i-k]] == 0:
                del hash[nums[i-k]]
            s += nums[i]
            hash[nums[i]] = hash.get(nums[i],0) + 1
            if len(hash) == k:
                m = max(m,s)
        return m

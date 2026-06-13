''' 
No of all possible subsequences  = 2**n so for {3,5,5,6} all possible subsets are [3,6],[3,5,6],[3,5,6],[3,5,5,6] which is 2**2 '''

class Solution:
    def numSubseq(self, nums: List[int], target: int) -> int:
        if len(nums) < 2 and nums[0]*2 <= target:
            return 1
        nums.sort()
        start,end = 0,len(nums) - 1
        count = 0
        while start <= end:
            if nums[start] + nums[end] <= target:
                count += 2**(end - start)
                start += 1
            else:
                end -= 1
            
            
        return count % 1000000007
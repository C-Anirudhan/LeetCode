class Solution:
    def trap(self, height: List[int]) -> int:
        if not height:
            return 0
        ans = 0
        start,end = 0,len(height) - 1
        left,right = height[start],height[end]
        while start < end:
            if height[start] < height[end]:
                left = max(height[start],left)

                ans += (left - height[start])
                start += 1
            else:
                right = max(height[end],right)
                ans += (right - height[end])
                end -= 1
        return ans

        
            
            

            
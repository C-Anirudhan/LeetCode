class Solution:
    def thirdMax(self, nums: List[int]) -> int:
        first = second = third = None
        for i in nums:
            if i == first or i == second or i == third:
                continue
            if first is None:
                first = i
            elif second is None:
                if i > first:
                    second = first
                    first = i
                else:
                    second = i
            elif third is None:
                if i > first:
                    third  = second
                    second = first
                    first = i
                elif i > second:
                    third = second
                    second = i
                else:
                    third = i
            elif i > first:
                third = second
                second = first
                first = i
            elif i > second:
                third = second
                second = i
            elif i > third:
                third = i
        return third if third is not None else first
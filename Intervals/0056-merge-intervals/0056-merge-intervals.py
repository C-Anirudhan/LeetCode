class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        intervals.sort()
        ans = [intervals[0]]

        for i in range(1,len(intervals)):
            s,e = ans[-1]
            st,end = intervals[i]
            if st <= e:
                ans[-1] = [s,max(e,end)]
            else:
                ans.append(intervals[i])
        return ans
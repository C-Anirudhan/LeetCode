class Solution:
    def intervalIntersection(self, firstList: List[List[int]], secondList: List[List[int]]) -> List[List[int]]:
        i,j = 0,0
        ans = []
        while i < len(firstList) and j < len(secondList):
            st = max(firstList[i][0],secondList[j][0])
            end = min(firstList[i][1],secondList[j][1])
            if st <= end:
                ans.append([st,end])
            if firstList[i][1] <=secondList[j][1]:
                i += 1
            else:
                j += 1
        return ans
class Solution:
    def numberOfBoomerangs(self, points: List[List[int]]) -> int:
        c = 0
        for i in range(len(points)):
            count = {}
            x1,y1 = points[i]
            for j in range(len(points)):
                if i == j:
                    continue
                x2,y2 = points[j]
                d = (x1 - x2)**2 + (y1 - y2)**2
                count[d] = count.get(d,0) + 1
            for x in count:
                if count[x] != 1:
                    c += (count[x] * (count[x]-1))
        return c
                
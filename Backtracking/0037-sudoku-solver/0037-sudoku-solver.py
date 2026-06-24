class Solution:
    def solveSudoku(self, board: List[List[str]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        row = defaultdict(set)
        col = defaultdict(set)
        box = defaultdict(set)
        empty = []

        for i in range(9):
            for j in range(9):
                if board[i][j] == ".":
                    empty.append((i,j))
                else:
                    row[i].add(board[i][j])
                    col[j].add(board[i][j])
                    b = (i//3,j//3)
                    box[b].add(board[i][j])

        n = len(empty)
        def solve(i):
            if i == n:
                return True
            r,c = empty[i]
            b = (r//3,c//3)
            for j in map(str,range(1,10)):
                if j not in row[r] and j not in col[c] and j not in box[b]:
                    board[r][c] = j 
                    row[r].add(j)
                    col[c].add(j)
                    box[b].add(j)

                    if solve(i+1):
                        return True

                    row[r].remove(j)
                    col[c].remove(j)
                    box[b].remove(j)
                    board[r][c] = "."
            return False

        solve(0)

            
            


        

            


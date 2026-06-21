# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def deleteDuplicates(self, head: Optional[ListNode]) -> Optional[ListNode]:
        prev = None
        ptr = head
        while ptr != None:
            if prev is not None and prev.val == ptr.val:
                prev.next = ptr.next
            prev = ptr
            ptr = ptr.next
        return head


# Definition for singly-linked list.
# class ListNode:
#     def __init__(self, val=0, next=None):
#         self.val = val
#         self.next = next
class Solution:
    def removeNthFromEnd(self, head: Optional[ListNode], n: int) -> Optional[ListNode]:
        slow = fast = head
        while fast.next != None:
            if n <= 0:
                slow = slow.next
            fast = fast.next
            n -= 1
            if n > 0 and fast.next is None:
                return head.next
        if n <= 0:
            slow.next = slow.next.next
            return head
        else:
            return head.next
'''
Created on 12.09.2023

@author: wf
'''
from nicepdf.pdftool import DoublePage
from tests.basetest import Basetest

class TestBookletPageNumbers(Basetest):
    """
    test the booklet page numbers
    """

    test_data = {
        # total_pages: [(index, from_binder, (expected_left, expected_right)), ...]
        100: [
            (0, False, (100, 1)),
            (2, False, (98, 3)),
            (4, False, (96, 5)),
            (1, False, (2, 99)),
            (3, False, (4, 97)),
            (0, True, (50, 51)),
            (2, True, (48, 53)),
            (4, True, (46, 55)),
            (1, True, (52, 49)),
            (3, True, (54, 47)),
            (5, True, (56, 45))
        ],
        8: [
            (0, False, (8, 1)),
            (2, False, (6, 3)),
            (1, False, (2, 7)),
            (3, False, (4, 5)),
            (0, True, (4, 5)),
            (2, True, (2, 7)),
            (1, True, (6, 3)),
            (3, True, (8, 1))
        ]
    }

    def test_booklet_page_numbers(self):
        """
        test the booklet numbering
        """
        for total_pages, tests in self.test_data.items():
            for index, from_binder, expected in tests:
                with self.subTest(total_pages=total_pages, index=index, from_binder=from_binder):
                    result = DoublePage.calculate_booklet_page_numbers(index, total_pages, from_binder)
                    msg=f"Testing total pages:{total_pages} index: {index} from_binder: {from_binder}"
                    self.assertEqual(result, expected,msg)
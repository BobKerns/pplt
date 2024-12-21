"""
This type stub file was generated by pyright.
"""

class matrix_class:
    def __init__(self) -> None:
        ...
    
    def set_size(self, cols, rows): # -> None:
        ...
    
    def update_size(self): # -> None:
        ...
    
    def set_axes_color(self, color=...): # -> None:
        ...
    
    def set_canvas_area(self, col1, col2, row1, row2): # -> None:
        ...
    
    def set_canvas_color(self, color=...): # -> None:
        ...
    
    def in_canvas(self, col, row): # -> bool:
        ...
    
    def set_matrices(self): # -> None:
        ...
    
    def legal(self, col, row): # -> bool:
        ...
    
    def get_marker(self, col, row):
        ...
    
    def get_marker_row(self, row):
        ...
    
    def get_marker_col(self, col): # -> list[Any]:
        ...
    
    def set_marker(self, col, row, marker): # -> None:
        ...
    
    def set_fullground(self, col, row, fullground=...): # -> None:
        ...
    
    def set_background(self, col, row, background=...): # -> None:
        ...
    
    def set_style(self, col, row, style=...): # -> None:
        ...
    
    def insert_element(self, col, row, marker, fullground=..., style=..., background=..., check_canvas=...): # -> None:
        ...
    
    def add_horizontal_string(self, col, row, string, fullground=..., style=..., background=..., alignment=..., check_space=..., check_canvas=...): # -> bool:
        ...
    
    def add_vertical_string(self, col, row, string, fullground=..., style=..., background=..., alignment=..., check_canvas=...): # -> None:
        ...
    
    def add_multiple_horizontal_strings(self, col, row, string, fullground=..., style=..., background=..., alignment=..., check_space=..., check_canvas=...): # -> None:
        ...
    
    def add_multiple_vertical_strings(self, col, row, string, fullground=..., style=..., background=..., alignment=..., check_canvas=...): # -> None:
        ...
    
    def get_colors(self, col, row): # -> list[Any]:
        ...
    
    def set_canvas(self): # -> str:
        ...
    
    def get_canvas(self): # -> str:
        ...
    
    def hstack(self, extra): # -> None:
        ...
    
    def vstack(self, extra): # -> None:
        ...
    
    def to_html(self): # -> str:
        ...
    


def join_matrices(matrices): # -> matrix_class:
    ...

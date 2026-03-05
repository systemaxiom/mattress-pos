import ttkbootstrap as tb
from negotiator import NegotiatorFrame
from calculator import CalculatorFrame



class CloserSuite(tb.Toplevel):
    def __init__(self, parent, cart, spiff_data, roster_data, on_finalize, store_name):
        super().__init__(title=f"Axiom Closer Suite | {store_name}", size=(1200, 800))
        self.position_center()
        main_container = tb.Frame(self, padding=10)
        main_container.pack(fill='both', expand=True)
        
        self.neg_pane = NegotiatorFrame(
            main_container, 
            cart=cart, 
            spiff_data=spiff_data, 
            roster_data=roster_data,
            on_finalize=on_finalize
        )
        self.neg_pane.pack(side='left', fill='both', expand=True, padx=(10,3))
        
        calc_wrapper = tb.LabelFrame(main_container, text=" Sales Math ")
        calc_wrapper.pack(side='right', fill='y', padx=(5,2))

        self.calc_pane = CalculatorFrame(calc_wrapper, target_neg=self.neg_pane)
        self.calc_pane.pack(fill='both', expand=True)
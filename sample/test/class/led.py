import sys
import os

from veriloggen import *

class Led(Module):
    def __init__(self, name='blinkled'):
        Module.__init__(self, name)
        self.width = self.Parameter('WIDTH', 8)
        self.clk = self.Input('CLK')
        self.rst = self.Input('RST')
        self.led = self.OutputReg('LED', self.width)
        self.count = self.Reg('count', 32)

        self.Always(Posedge(self.clk))(
            If(self.rst)(
                self.count(0)
            ).Else(
                self.count(self.count + 1)
            ))
        
        self.Always(Posedge(self.clk))(
            If(self.rst)(
                self.led(0)
            ).Else(
                If(self.count == 1024 - 1)(
                    self.led(self.led + 1)
                )
            ))
        
if __name__ == '__main__':
    led_module = Led()
    led_code = led_module.to_verilog()
    print(led_code)
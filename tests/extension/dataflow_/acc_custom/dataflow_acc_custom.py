from __future__ import absolute_import
from __future__ import print_function
import sys
import os

# the next line can be removed after installation
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from veriloggen import *

def mkLed():
    m = Module('blinkled')
    clk = m.Input('CLK')
    rst = m.Input('RST')
    x = m.Input('x', 32)
    vx = m.Input('vx')
    rx = m.Output('rx')
    y = m.Output('y', 32)
    vy = m.Output('vy')
    ry = m.Input('ry')
    prst = m.Input('prst')
    
    df = Dataflow(m, 'df', clk, rst)

    px = df.input(x, valid=vx, ready=rx)

    # custom operator: should return vtypes._Numeric object
    def op_max(left, right):
        return Cond(left > right, left, right)
    
    psum = df.acc_custom(px, op_max, initval=0, resetcond=prst, label='custom')
    psum.output(y, valid=vy, ready=ry)
    
    df.make_always()
    
    try:
        df.draw_graph()
    except:
        print('Dataflow graph could not be generated.', file=sys.stderr)

    return m

def mkTest(numports=8):
    m = Module('test')

    # target instance
    led = mkLed()
    
    # copy paras and ports
    params = m.copy_params(led)
    ports = m.copy_sim_ports(led)

    clk = ports['CLK']
    rst = ports['RST']
    x = ports['x']
    vx = ports['vx']
    rx = ports['rx']
    y = ports['y']
    vy = ports['vy']
    ry = ports['ry']
    prst = ports['prst']
    
    uut = m.Instance(led, 'uut',
                     params=m.connect_params(led),
                     ports=m.connect_ports(led))

    reset_done = m.Reg('reset_done', initval=0)
    
    reset_stmt = []
    reset_stmt.append( reset_done(0) )
    reset_stmt.append( prst(0) )
    reset_stmt.append( x(0) )
    reset_stmt.append( vx(0) )
    reset_stmt.append( ry(0) )
    
    simulation.setup_waveform(m, uut)
    simulation.setup_clock(m, clk, hperiod=5)
    init = simulation.setup_reset(m, rst, reset_stmt, period=100)

    nclk = simulation.next_clock
    
    init.add(
        Delay(1000),
        reset_done(1),
        nclk(clk),
        Delay(10000),
        Systask('finish'),
    )

    x_count = m.TmpReg(32, initval=0)
    y_count = m.TmpReg(32, initval=0)
    

    xfsm = FSM(m, 'xfsm', clk, rst)
    xfsm.add(vx(0))
    xfsm.goto_next(cond=reset_done)
    xfsm.add(vx(1))
    xfsm.add(x.inc(), cond=rx)
    xfsm.add(x_count.inc(), cond=rx)
    xfsm.goto_next(cond=AndList(x_count==10, rx))
    xfsm.add(vx(0))
    xfsm.make_always()
    
    
    yfsm = FSM(m, 'yfsm', clk, rst)
    yfsm.add(ry(0))
    yfsm.goto_next(cond=reset_done)
    yfsm.goto_next()
    yinit= yfsm.current()
    yfsm.add(ry(1), cond=vy)
    yfsm.goto_next(cond=vy)
    for i in range(10):
        yfsm.add(ry(0))
        yfsm.goto_next()
    yfsm.goto(yinit)
    yfsm.make_always()


    m.Always(Posedge(clk))(
        If(reset_done)(
            If(AndList(vx, rx))(
                Systask('display', 'x=%d', x)
            ),
            If(AndList(vy, ry))(
                Systask('display', 'y=%d', y)
            )
        )
    )

    return m
    
if __name__ == '__main__':
    test = mkTest()
    verilog = test.to_verilog('tmp.v')
    print(verilog)

    # run simulator (Icarus Verilog)
    sim = simulation.Simulator(test)
    rslt = sim.run() # display=False
    #rslt = sim.run(display=True)
    print(rslt)

    # launch waveform viewer (GTKwave)
    #sim.view_waveform() # background=False
    #sim.view_waveform(background=True)
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer, ClockCycles


segments = [ 63, 6, 91, 79, 102, 109, 124, 7, 127, 103 ]

@cocotb.test()
async def test_loopback_ericsmi(dut):
    dut._log.info("start")
    clock = Clock(dut.clk, 10, units="us")
    cocotb.start_soon(clock.start())

    # Initial condition from MUX, tile not selected
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut._log.info("reset")
    dut.rst_n.value = 0
    dut.ena.value = 0

     # Clear X to make cocotb happy 

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    dut.rst_n.value = 0

    await ClockCycles(dut.clk, 1)
    assert 0x80 & dut.uo_out.value == 0x00

    # Select this tile

    dut.ena.value = 1  
    await ClockCycles(dut.clk, 1)
    assert 0x80 & dut.uo_out.value == 0x80

    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)
    assert 0x80 & (dut.uo_out.value) == 0x00

    dut.ui_in.value = 0xF0
    await ClockCycles(dut.clk, 1)
    assert 0x80 & (dut.uo_out.value) == 0x80

    dut.ui_in.value = 0xE0
    await ClockCycles(dut.clk, 1)
    assert 0x80 & (dut.uo_out.value) == 0x00

    dut._log.info("PASS: buffer ena and &ui_in[7:4]")

    for k in range(2):
        # default behavior ignores rst_n
        dut.rst_n.value = k
        for i in range(4):
            dut.ui_in.value = i
            await ClockCycles(dut.clk, 1)
            v = int(dut.uo_out.value)
            for j in range(7):
                assert 0x1 & v == 0x1 & i
                v >>= 1

    dut._log.info("PASS: buffer i[0]")

    for i in range(8):
        for j in range(8):
            if i != j:
                dut.ui_in.value = 0xF0
                dut.uio_in.value = 0x40 | (j<<3) | i
                await ClockCycles(dut.clk, 1)
                dut.ui_in.value = 0
                await ClockCycles(dut.clk, 1)
                assert dut.uio_in.value == dut.uio_out.value
                for k in range(2):
                    dut.ui_in.value = k << i # assign D
                    await ClockCycles(dut.clk, 1) # make posedge
                    dut.ui_in.value = (k << i)|(1<<j)
                    await ClockCycles(dut.clk, 1)
                    dut.ui_in.value = k << i # make negedge
                    await ClockCycles(dut.clk, 1)
                    assert k == 0x1 & int(dut.uo_out.value)
                    assert k == 0x1 & (int(dut.uo_out.value) >>4)

    dut._log.info("PASS: Race Bits")

    dut.ui_in.value = 0xF0
    # enable bypass and use sel0=1
    dut.uio_in.value = 0xC1
    await ClockCycles(dut.clk, 1)
    dut.ui_in.value = 0
    await ClockCycles(dut.clk, 1)
    assert 0xC1 & int(dut.uio_out.value)

    for i in range(4):
        dut.ui_in.value = i
        await ClockCycles(dut.clk, 1)
        assert i & 0x1 == int(dut.uo_out.value) >> 6
        assert i >> 1 == 0x1 & int(dut.uo_out.value)

    dut._log.info("PASS: Bypass Mode")
    
    dut.ui_in.value = 0xF0 # turn on jitter flop
    await ClockCycles(dut.clk, 1)

    prev = int(dut.uo_out.value) >> 5
    await ClockCycles(dut.clk, 1)
    next = int(dut.uo_out.value) >> 5

    assert prev != next 

    dut.ui_in.value = 0xE0 # turn off jitter flop
    await ClockCycles(dut.clk, 1)

    prev = int(dut.uo_out.value) >> 5
    await ClockCycles(dut.clk, 1)
    next = int(dut.uo_out.value) >> 5

    assert prev == next 

    dut._log.info("PASS: clk div2")

